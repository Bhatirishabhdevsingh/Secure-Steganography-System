package com.securesteganography.android.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable

private val LightColors = lightColorScheme(
    primary = DeepTeal,
    secondary = Coral,
    tertiary = MintGlow,
    background = SoftSand,
    surface = androidx.compose.ui.graphics.Color.White,
)

private val DarkColors = darkColorScheme(
    primary = MintGlow,
    secondary = Coral,
    background = Slate,
    surface = DeepTeal,
)

@Composable
fun SecureSteganographyTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = LightColors,
        content = content,
    )
}
