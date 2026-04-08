package com.securesteganography.android

import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts.CreateDocument
import androidx.activity.result.contract.ActivityResultContracts.OpenDocument
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Tab
import androidx.compose.material3.TabRow
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.securesteganography.android.stego.PayloadPackage
import com.securesteganography.android.stego.SteganographyCodec
import com.securesteganography.android.stego.SteganographyException
import com.securesteganography.android.ui.theme.SecureSteganographyTheme
import com.securesteganography.android.util.UriUtils
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        setContent {
            SecureSteganographyTheme {
                SteganographyApp()
            }
        }
    }
}

@Composable
private fun ComponentActivity.SteganographyApp() {
    val scope = rememberCoroutineScope()
    val snackbarHostState = remember { SnackbarHostState() }
    var selectedTab by rememberSaveable { mutableStateOf(0) }

    var carrierUri by remember { mutableStateOf<Uri?>(null) }
    var carrierName by rememberSaveable { mutableStateOf("") }
    var payloadFileUri by remember { mutableStateOf<Uri?>(null) }
    var payloadFileName by rememberSaveable { mutableStateOf("") }
    var stegoUri by remember { mutableStateOf<Uri?>(null) }
    var stegoName by rememberSaveable { mutableStateOf("") }

    var encodeMode by rememberSaveable { mutableStateOf("text") }
    var secretMessage by rememberSaveable { mutableStateOf("") }
    var encodePassword by rememberSaveable { mutableStateOf("") }
    var decodePassword by rememberSaveable { mutableStateOf("") }
    var statusMessage by rememberSaveable { mutableStateOf("Choose a mode and start working.") }
    var extractedPreview by rememberSaveable { mutableStateOf("") }
    var isBusy by rememberSaveable { mutableStateOf(false) }

    var pendingEncodedPng by remember { mutableStateOf<ByteArray?>(null) }
    var pendingEncodedName by rememberSaveable { mutableStateOf("secure_stego.png") }
    var extractedPayload by remember { mutableStateOf<PayloadPackage?>(null) }

    val pickCarrierLauncher = rememberLauncherForActivityResult(OpenDocument()) { uri ->
        if (uri != null) {
            contentResolver.takePersistableUriPermissionSafely(uri)
            carrierUri = uri
            carrierName = UriUtils.displayName(contentResolver, uri)
            statusMessage = "Carrier image ready: $carrierName"
        }
    }

    val pickPayloadFileLauncher = rememberLauncherForActivityResult(OpenDocument()) { uri ->
        if (uri != null) {
            contentResolver.takePersistableUriPermissionSafely(uri)
            payloadFileUri = uri
            payloadFileName = UriUtils.displayName(contentResolver, uri)
            statusMessage = "Payload file ready: $payloadFileName"
        }
    }

    val pickStegoLauncher = rememberLauncherForActivityResult(OpenDocument()) { uri ->
        if (uri != null) {
            contentResolver.takePersistableUriPermissionSafely(uri)
            stegoUri = uri
            stegoName = UriUtils.displayName(contentResolver, uri)
            statusMessage = "Stego image ready: $stegoName"
        }
    }

    val saveEncodedLauncher = rememberLauncherForActivityResult(CreateDocument("image/png")) { uri ->
        val bytes = pendingEncodedPng
        if (uri != null && bytes != null) {
            scope.launch {
                try {
                    withContext(Dispatchers.IO) {
                        contentResolver.openOutputStream(uri)?.use { output ->
                            output.write(bytes)
                        } ?: error("Could not open target file.")
                    }
                    statusMessage = "Encoded PNG saved successfully."
                    pendingEncodedPng = null
                } catch (error: Exception) {
                    statusMessage = error.userFacingMessage()
                }
            }
        }
    }

    val saveExtractedLauncher = rememberLauncherForActivityResult(CreateDocument("*/*")) { uri ->
        val payload = extractedPayload
        if (uri != null && payload != null) {
            scope.launch {
                try {
                    withContext(Dispatchers.IO) {
                        contentResolver.openOutputStream(uri)?.use { output ->
                            output.write(payload.data)
                        } ?: error("Could not open target file.")
                    }
                    statusMessage = "Extracted file saved successfully."
                } catch (error: Exception) {
                    statusMessage = error.userFacingMessage()
                }
            }
        }
    }

    LaunchedEffect(statusMessage) {
        if (statusMessage.isNotBlank()) {
            snackbarHostState.showSnackbar(statusMessage)
        }
    }

    Scaffold(
        snackbarHost = { SnackbarHost(snackbarHostState) },
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .background(MaterialTheme.colorScheme.background)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            Text(
                text = "Secure Steganography",
                style = MaterialTheme.typography.headlineMedium,
            )
            Text(
                text = "Android app for hiding text or files inside images with password protection.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            TabRow(selectedTabIndex = selectedTab) {
                Tab(
                    selected = selectedTab == 0,
                    onClick = { selectedTab = 0 },
                    text = { Text("Encode") },
                )
                Tab(
                    selected = selectedTab == 1,
                    onClick = { selectedTab = 1 },
                    text = { Text("Decode") },
                )
            }

            if (selectedTab == 0) {
                Card(shape = RoundedCornerShape(24.dp)) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        Text("Carrier image", style = MaterialTheme.typography.titleMedium)
                        Text(carrierName.ifBlank { "No image selected" })
                        Button(
                            onClick = { pickCarrierLauncher.launch(arrayOf("image/*")) },
                            enabled = !isBusy,
                        ) {
                            Text("Choose image")
                        }

                        Text("Payload type", style = MaterialTheme.typography.titleMedium)
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            FilterChip(
                                selected = encodeMode == "text",
                                onClick = { encodeMode = "text" },
                                label = { Text("Text") },
                            )
                            FilterChip(
                                selected = encodeMode == "file",
                                onClick = { encodeMode = "file" },
                                label = { Text("File") },
                            )
                        }

                        if (encodeMode == "text") {
                            OutlinedTextField(
                                value = secretMessage,
                                onValueChange = { secretMessage = it },
                                modifier = Modifier.fillMaxWidth(),
                                minLines = 4,
                                label = { Text("Secret message") },
                            )
                        } else {
                            Text(payloadFileName.ifBlank { "No file selected" })
                            Button(
                                onClick = { pickPayloadFileLauncher.launch(arrayOf("*/*")) },
                                enabled = !isBusy,
                            ) {
                                Text("Choose file")
                            }
                        }

                        OutlinedTextField(
                            value = encodePassword,
                            onValueChange = { encodePassword = it },
                            modifier = Modifier.fillMaxWidth(),
                            label = { Text("Password") },
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                        )

                        Button(
                            onClick = {
                                scope.launch {
                                    isBusy = true
                                    try {
                                        val payload = withContext(Dispatchers.IO) {
                                            when (encodeMode) {
                                                "text" -> {
                                                    if (secretMessage.isBlank()) error("Secret message required.")
                                                    PayloadPackage.text(secretMessage)
                                                }

                                                else -> {
                                                    val uri = payloadFileUri ?: error("Choose a file to hide.")
                                                    PayloadPackage.file(
                                                        fileName = UriUtils.displayName(contentResolver, uri),
                                                        mimeType = contentResolver.getType(uri) ?: "application/octet-stream",
                                                        data = UriUtils.readBytes(contentResolver, uri),
                                                    )
                                                }
                                            }
                                        }

                                        val carrier = carrierUri ?: error("Choose a carrier image first.")
                                        if (encodePassword.isBlank()) error("Password is required.")

                                        val result = withContext(Dispatchers.IO) {
                                            SteganographyCodec.encode(
                                                contentResolver = contentResolver,
                                                carrierUri = carrier,
                                                payload = payload,
                                                password = encodePassword,
                                            )
                                        }

                                        pendingEncodedPng = result.pngBytes
                                        pendingEncodedName = result.suggestedFileName
                                        statusMessage = "Encoding complete. Choose where to save the PNG."
                                        saveEncodedLauncher.launch(result.suggestedFileName)
                                    } catch (error: Exception) {
                                        statusMessage = error.userFacingMessage()
                                    } finally {
                                        isBusy = false
                                    }
                                }
                            },
                            enabled = !isBusy,
                            modifier = Modifier.fillMaxWidth(),
                        ) {
                            Text(if (isBusy) "Working..." else "Encode & Save PNG")
                        }
                    }
                }
            } else {
                Card(shape = RoundedCornerShape(24.dp)) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        Text("Stego image", style = MaterialTheme.typography.titleMedium)
                        Text(stegoName.ifBlank { "No stego image selected" })
                        Button(
                            onClick = { pickStegoLauncher.launch(arrayOf("image/*")) },
                            enabled = !isBusy,
                        ) {
                            Text("Choose PNG")
                        }

                        OutlinedTextField(
                            value = decodePassword,
                            onValueChange = { decodePassword = it },
                            modifier = Modifier.fillMaxWidth(),
                            label = { Text("Password") },
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                        )

                        Button(
                            onClick = {
                                scope.launch {
                                    isBusy = true
                                    try {
                                        val imageUri = stegoUri ?: error("Choose a stego image first.")
                                        if (decodePassword.isBlank()) error("Password is required.")

                                        val decoded = withContext(Dispatchers.IO) {
                                            SteganographyCodec.decode(
                                                contentResolver = contentResolver,
                                                stegoUri = imageUri,
                                                password = decodePassword,
                                            )
                                        }
                                        extractedPayload = decoded
                                        extractedPreview =
                                            if (decoded.payloadType == PayloadPackage.TYPE_TEXT) {
                                                decoded.data.toString(Charsets.UTF_8)
                                            } else {
                                                "File recovered: ${decoded.fileName} (${decoded.mimeType})"
                                            }
                                        statusMessage = "Decoding complete."
                                    } catch (error: Exception) {
                                        extractedPayload = null
                                        extractedPreview = ""
                                        statusMessage = error.userFacingMessage()
                                    } finally {
                                        isBusy = false
                                    }
                                }
                            },
                            enabled = !isBusy,
                            modifier = Modifier.fillMaxWidth(),
                        ) {
                            Text(if (isBusy) "Working..." else "Decode")
                        }

                        if (extractedPreview.isNotBlank()) {
                            Box(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .background(
                                        color = MaterialTheme.colorScheme.surfaceVariant,
                                        shape = RoundedCornerShape(20.dp),
                                    )
                                    .padding(16.dp),
                            ) {
                                Text(extractedPreview)
                            }
                        }

                        val payload = extractedPayload
                        if (payload != null && payload.payloadType == PayloadPackage.TYPE_FILE) {
                            Button(
                                onClick = {
                                    saveExtractedLauncher.launch(payload.fileName.ifBlank { "extracted.bin" })
                                },
                                enabled = !isBusy,
                            ) {
                                Text("Save extracted file")
                            }
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(8.dp))
            TextButton(
                onClick = {
                    carrierUri = null
                    carrierName = ""
                    payloadFileUri = null
                    payloadFileName = ""
                    stegoUri = null
                    stegoName = ""
                    secretMessage = ""
                    encodePassword = ""
                    decodePassword = ""
                    extractedPayload = null
                    extractedPreview = ""
                    pendingEncodedPng = null
                    statusMessage = "Form reset."
                },
            ) {
                Text("Reset")
            }
        }
    }
}

private fun ComponentActivity.takePersistableUriPermissionSafely(uri: Uri) {
    runCatching {
        contentResolver.takePersistableUriPermission(
            uri,
            android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION,
        )
    }
}

private fun Throwable.userFacingMessage(): String {
    return when (this) {
        is SteganographyException -> message ?: "Steganography failed."
        else -> message ?: "Operation failed."
    }
}
