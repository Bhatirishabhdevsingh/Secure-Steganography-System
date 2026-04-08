package com.securesteganography.android.stego

data class PayloadPackage(
    val payloadType: String,
    val fileName: String,
    val mimeType: String,
    val data: ByteArray,
) {
    companion object {
        const val TYPE_TEXT = "text"
        const val TYPE_FILE = "file"

        fun text(message: String): PayloadPackage {
            return PayloadPackage(
                payloadType = TYPE_TEXT,
                fileName = "message.txt",
                mimeType = "text/plain",
                data = message.toByteArray(Charsets.UTF_8),
            )
        }

        fun file(fileName: String, mimeType: String, data: ByteArray): PayloadPackage {
            return PayloadPackage(
                payloadType = TYPE_FILE,
                fileName = fileName,
                mimeType = mimeType,
                data = data,
            )
        }
    }
}
