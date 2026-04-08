package com.securesteganography.android.stego

import android.content.ContentResolver
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import java.io.ByteArrayOutputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.security.MessageDigest
import java.security.SecureRandom
import java.util.Random
import javax.crypto.Cipher
import javax.crypto.SecretKeyFactory
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.PBEKeySpec
import javax.crypto.spec.SecretKeySpec
import kotlin.math.abs

object SteganographyCodec {
    private const val PBKDF2_ITERATIONS = 250_000
    private const val KEY_LENGTH_BITS = 256
    private val PUBLIC_HEADER_MAGIC = "SSG1".toByteArray(Charsets.UTF_8)
    private val BUNDLE_HEADER_MAGIC = "BDL1".toByteArray(Charsets.UTF_8)
    private const val PUBLIC_HEADER_SIZE = 57
    private const val BUNDLE_HEADER_SIZE = 17

    data class EncodeResult(
        val pngBytes: ByteArray,
        val suggestedFileName: String,
    )

    fun encode(
        contentResolver: ContentResolver,
        carrierUri: Uri,
        payload: PayloadPackage,
        password: String,
    ): EncodeResult {
        val bitmap = readBitmap(contentResolver, carrierUri)
        val bundle = buildBundle(payload)
        val salt = randomBytes(16)
        val nonce = randomBytes(12)
        val shuffleSalt = salt.reversedArray()
        val ciphertext = encrypt(bundle, password, salt, nonce)
        val publicHeader = buildPublicHeader(salt, shuffleSalt, nonce, ciphertext.size.toLong())
        val totalBits = (publicHeader.size + ciphertext.size) * 8
        val rgbCapacityBits = bitmap.width * bitmap.height * 3

        if (totalBits > rgbCapacityBits) {
            throw CapacityException("Carrier image is too small for this payload.")
        }

        val mutable = bitmap.copy(Bitmap.Config.ARGB_8888, true)
        val pixels = IntArray(mutable.width * mutable.height)
        mutable.getPixels(pixels, 0, mutable.width, 0, 0, mutable.width, mutable.height)

        val headerBits = bytesToBits(publicHeader)
        val payloadBits = bytesToBits(ciphertext)
        val reservedBits = PUBLIC_HEADER_SIZE * 8

        embedSequentialBits(pixels, headerBits)
        val positions = buildPayloadPositions(pixels, password, shuffleSalt, payloadBits.size, reservedBits)
        embedBitsAtPositions(pixels, positions, payloadBits)

        mutable.setPixels(pixels, 0, mutable.width, 0, 0, mutable.width, mutable.height)
        val output = ByteArrayOutputStream()
        mutable.compress(Bitmap.CompressFormat.PNG, 100, output)

        return EncodeResult(
            pngBytes = output.toByteArray(),
            suggestedFileName = "secure_stego.png",
        )
    }

    fun decode(
        contentResolver: ContentResolver,
        stegoUri: Uri,
        password: String,
    ): PayloadPackage {
        val bitmap = readBitmap(contentResolver, stegoUri)
        val pixels = IntArray(bitmap.width * bitmap.height)
        bitmap.getPixels(pixels, 0, bitmap.width, 0, 0, bitmap.width, bitmap.height)

        val headerBytes = bitsToBytes(readSequentialBits(pixels, PUBLIC_HEADER_SIZE * 8))
        val header = parsePublicHeader(headerBytes)
        val payloadBitsLength = header.ciphertextLength.toInt() * 8
        val positions = buildPayloadPositions(pixels, password, header.shuffleSalt, payloadBitsLength, PUBLIC_HEADER_SIZE * 8)
        val ciphertext = bitsToBytes(readBitsAtPositions(pixels, positions))
        val bundle = decrypt(ciphertext, password, header.salt, header.nonce)
        return parseBundle(bundle)
    }

    private fun readBitmap(contentResolver: ContentResolver, uri: Uri): Bitmap {
        val options = BitmapFactory.Options().apply {
            inPreferredConfig = Bitmap.Config.ARGB_8888
        }
        val bytes = contentResolver.openInputStream(uri)?.use { it.readBytes() }
            ?: throw InvalidImageException("Could not read selected image.")
        return BitmapFactory.decodeByteArray(bytes, 0, bytes.size, options)
            ?: throw InvalidImageException("Unsupported image format.")
    }

    private fun randomBytes(length: Int): ByteArray = ByteArray(length).also { SecureRandom().nextBytes(it) }

    private fun deriveKey(password: String, salt: ByteArray): ByteArray {
        val factory = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256")
        val spec = PBEKeySpec(password.toCharArray(), salt, PBKDF2_ITERATIONS, KEY_LENGTH_BITS)
        return factory.generateSecret(spec).encoded
    }

    private fun encrypt(plainBytes: ByteArray, password: String, salt: ByteArray, nonce: ByteArray): ByteArray {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        val key = SecretKeySpec(deriveKey(password, salt), "AES")
        cipher.init(Cipher.ENCRYPT_MODE, key, GCMParameterSpec(128, nonce))
        return cipher.doFinal(plainBytes)
    }

    private fun decrypt(cipherBytes: ByteArray, password: String, salt: ByteArray, nonce: ByteArray): ByteArray {
        return try {
            val cipher = Cipher.getInstance("AES/GCM/NoPadding")
            val key = SecretKeySpec(deriveKey(password, salt), "AES")
            cipher.init(Cipher.DECRYPT_MODE, key, GCMParameterSpec(128, nonce))
            cipher.doFinal(cipherBytes)
        } catch (_: Exception) {
            throw AuthenticationException("Password is incorrect or the hidden data was modified.")
        }
    }

    private fun deriveShuffleSeed(password: String, salt: ByteArray): Long {
        val keyMaterial = deriveKey(password, salt)
        val digest = MessageDigest.getInstance("SHA-256").digest(keyMaterial + salt)
        return ByteBuffer.wrap(digest.copyOfRange(0, 8)).order(ByteOrder.BIG_ENDIAN).long
    }

    private fun buildBundle(payload: PayloadPackage): ByteArray {
        val fileNameBytes = payload.fileName.toByteArray(Charsets.UTF_8)
        val mimeBytes = payload.mimeType.toByteArray(Charsets.UTF_8)
        val header = ByteBuffer.allocate(BUNDLE_HEADER_SIZE).order(ByteOrder.BIG_ENDIAN).apply {
            put(BUNDLE_HEADER_MAGIC)
            put(if (payload.payloadType == PayloadPackage.TYPE_TEXT) 0 else 1)
            putShort(fileNameBytes.size.toShort())
            putShort(mimeBytes.size.toShort())
            putLong(payload.data.size.toLong())
        }.array()
        return header + fileNameBytes + mimeBytes + payload.data
    }

    private fun parseBundle(bundle: ByteArray): PayloadPackage {
        if (bundle.size < BUNDLE_HEADER_SIZE) {
            throw InvalidImageException("Hidden data is incomplete or corrupted.")
        }

        val header = ByteBuffer.wrap(bundle, 0, BUNDLE_HEADER_SIZE).order(ByteOrder.BIG_ENDIAN)
        val magic = ByteArray(4).also { header.get(it) }
        if (!magic.contentEquals(BUNDLE_HEADER_MAGIC)) {
            throw InvalidImageException("Hidden data header is invalid.")
        }

        val payloadType = header.get().toInt()
        val nameLength = header.short.toInt() and 0xffff
        val mimeLength = header.short.toInt() and 0xffff
        val dataLength = header.long.toInt()

        var offset = BUNDLE_HEADER_SIZE
        val fileName = bundle.copyOfRange(offset, offset + nameLength).toString(Charsets.UTF_8)
        offset += nameLength
        val mimeType = bundle.copyOfRange(offset, offset + mimeLength).toString(Charsets.UTF_8)
        offset += mimeLength
        val data = bundle.copyOfRange(offset, offset + dataLength)

        return PayloadPackage(
            payloadType = if (payloadType == 0) PayloadPackage.TYPE_TEXT else PayloadPackage.TYPE_FILE,
            fileName = fileName,
            mimeType = mimeType.ifBlank { "application/octet-stream" },
            data = data,
        )
    }

    private fun buildPublicHeader(
        salt: ByteArray,
        shuffleSalt: ByteArray,
        nonce: ByteArray,
        ciphertextLength: Long,
    ): ByteArray {
        return ByteBuffer.allocate(PUBLIC_HEADER_SIZE).order(ByteOrder.BIG_ENDIAN).apply {
            put(PUBLIC_HEADER_MAGIC)
            put(1)
            put(salt)
            put(shuffleSalt)
            put(nonce)
            putLong(ciphertextLength)
        }.array()
    }

    private fun parsePublicHeader(bytes: ByteArray): PublicHeader {
        if (bytes.size < PUBLIC_HEADER_SIZE) {
            throw InvalidImageException("No valid Secure Steganography payload found.")
        }

        val buffer = ByteBuffer.wrap(bytes).order(ByteOrder.BIG_ENDIAN)
        val magic = ByteArray(4).also { buffer.get(it) }
        val version = buffer.get().toInt()
        if (!magic.contentEquals(PUBLIC_HEADER_MAGIC) || version != 1) {
            throw InvalidImageException("No valid Secure Steganography payload found.")
        }

        val salt = ByteArray(16).also { buffer.get(it) }
        val shuffleSalt = ByteArray(16).also { buffer.get(it) }
        val nonce = ByteArray(12).also { buffer.get(it) }
        val ciphertextLength = buffer.long
        return PublicHeader(salt, shuffleSalt, nonce, ciphertextLength)
    }

    private fun buildPayloadPositions(
        pixels: IntArray,
        password: String,
        shuffleSalt: ByteArray,
        bitLength: Int,
        reservedBits: Int,
    ): IntArray {
        val candidates = buildCandidateChannels(pixels).filter { it >= reservedBits }.toMutableList()
        if (candidates.size < bitLength) {
            throw CapacityException("Carrier image capacity is insufficient.")
        }

        val random = Random(deriveShuffleSeed(password, shuffleSalt))
        for (index in candidates.lastIndex downTo 1) {
            val swapIndex = random.nextInt(index + 1)
            val temp = candidates[index]
            candidates[index] = candidates[swapIndex]
            candidates[swapIndex] = temp
        }
        return candidates.take(bitLength).toIntArray()
    }

    private fun buildCandidateChannels(pixels: IntArray): IntArray {
        val pixelCount = pixels.size
        val scores = FloatArray(pixelCount)

        for (index in 0 until pixelCount) {
            val current = pixels[index]
            val currentGray = gray(current)
            val rightGray = gray(pixels[(index + 1) % pixelCount])
            val downGray = gray(pixels[(index + 64) % pixelCount])
            scores[index] = abs(currentGray - rightGray) + abs(currentGray - downGray)
        }

        val rankedPixels = (0 until pixelCount).sortedByDescending { scores[it] }
        val channels = IntArray(pixelCount * 3)
        var offset = 0
        for (pixelIndex in rankedPixels) {
            channels[offset++] = pixelIndex * 3
            channels[offset++] = pixelIndex * 3 + 1
            channels[offset++] = pixelIndex * 3 + 2
        }
        return channels
    }

    private fun gray(color: Int): Float {
        val r = (color shr 16) and 0xfe
        val g = (color shr 8) and 0xfe
        val b = color and 0xfe
        return (0.299f * r) + (0.587f * g) + (0.114f * b)
    }

    private fun embedSequentialBits(pixels: IntArray, bits: IntArray) {
        for (index in bits.indices) {
            setRgbBit(pixels, index, bits[index])
        }
    }

    private fun embedBitsAtPositions(pixels: IntArray, positions: IntArray, bits: IntArray) {
        for (index in bits.indices) {
            setRgbBit(pixels, positions[index], bits[index])
        }
    }

    private fun readSequentialBits(pixels: IntArray, count: Int): IntArray {
        return IntArray(count) { index -> readRgbBit(pixels, index) }
    }

    private fun readBitsAtPositions(pixels: IntArray, positions: IntArray): IntArray {
        return IntArray(positions.size) { index -> readRgbBit(pixels, positions[index]) }
    }

    private fun setRgbBit(pixels: IntArray, rgbPosition: Int, bit: Int) {
        val pixelIndex = rgbPosition / 3
        val channel = rgbPosition % 3
        val color = pixels[pixelIndex]
        val a = (color ushr 24) and 0xff
        var r = (color ushr 16) and 0xff
        var g = (color ushr 8) and 0xff
        var b = color and 0xff

        when (channel) {
            0 -> r = (r and 0xfe) or bit
            1 -> g = (g and 0xfe) or bit
            else -> b = (b and 0xfe) or bit
        }

        pixels[pixelIndex] = (a shl 24) or (r shl 16) or (g shl 8) or b
    }

    private fun readRgbBit(pixels: IntArray, rgbPosition: Int): Int {
        val pixelIndex = rgbPosition / 3
        val channel = rgbPosition % 3
        val color = pixels[pixelIndex]
        return when (channel) {
            0 -> (color shr 16) and 1
            1 -> (color shr 8) and 1
            else -> color and 1
        }
    }

    private fun bytesToBits(bytes: ByteArray): IntArray {
        val bits = IntArray(bytes.size * 8)
        var offset = 0
        for (byte in bytes) {
            val value = byte.toInt() and 0xff
            for (bit in 7 downTo 0) {
                bits[offset++] = (value shr bit) and 1
            }
        }
        return bits
    }

    private fun bitsToBytes(bits: IntArray): ByteArray {
        val output = ByteArray((bits.size + 7) / 8)
        for (index in bits.indices) {
            val byteIndex = index / 8
            val shift = 7 - (index % 8)
            output[byteIndex] = (output[byteIndex].toInt() or (bits[index] shl shift)).toByte()
        }
        return output
    }

    private data class PublicHeader(
        val salt: ByteArray,
        val shuffleSalt: ByteArray,
        val nonce: ByteArray,
        val ciphertextLength: Long,
    )
}
