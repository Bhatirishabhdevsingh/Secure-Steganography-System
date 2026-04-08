package com.securesteganography.android.util

import android.content.ContentResolver
import android.net.Uri
import android.provider.OpenableColumns

object UriUtils {
    fun displayName(contentResolver: ContentResolver, uri: Uri): String {
        contentResolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)?.use { cursor ->
            val index = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
            if (index >= 0 && cursor.moveToFirst()) {
                return cursor.getString(index) ?: "selected_file"
            }
        }
        return uri.lastPathSegment ?: "selected_file"
    }

    fun readBytes(contentResolver: ContentResolver, uri: Uri): ByteArray {
        return contentResolver.openInputStream(uri)?.use { it.readBytes() }
            ?: error("Could not open selected file.")
    }
}
