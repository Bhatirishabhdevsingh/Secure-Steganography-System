# Secure Steganography Android App

This folder contains a native Android Studio project for the steganography tool.

## Features

- Hide text inside an image
- Hide a file inside an image
- Protect payloads with a password
- Export the encoded image as PNG
- Decode text or files from a stego PNG

## Open In Android Studio

1. Open Android Studio.
2. Choose `Open`.
3. Select [`android-app/`](/home/kali/Desktop/vapt/steganography-tool/android-app).
4. Let Gradle sync.
5. Run on an emulator or Android device with Android 8.0+.

## Notes

- The Android app uses the same overall AES-GCM + PBKDF2 + LSB steganography approach as the main project.
- Output is saved as PNG because JPEG compression would damage hidden bits.
- I could scaffold the project locally, but full APK compilation was not verified here because Android SDK/device tooling is not available in this environment.
