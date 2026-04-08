# Secure Steganography System

## Title Page

**Project Title:** Secure Steganography System  
**Project Type:** Mini Project / Academic Project Report  
**Submitted By:** Rishabh dev Singh  
**Domain:** Cybersecurity / Information Security  

---

## Abstract

The Secure Steganography System is a practical cybersecurity project designed to hide secret text or files inside digital images while also protecting the hidden content through strong encryption. Traditional encryption can secure information, but it does not conceal the existence of the data. Steganography solves this problem by embedding secret information inside a carrier medium such as an image. In this project, both techniques are combined to provide a stronger and more realistic secure communication method.

The system first packages the user payload with metadata, encrypts it using AES-256-GCM, and then embeds the encrypted bytes into image pixels using randomized Least Significant Bit embedding. A password-derived seed controls the randomized placement, while PBKDF2-SHA256 strengthens password-based key generation. The project supports hiding both text messages and arbitrary files, and it allows recovery only when the correct password is supplied.

The implementation includes a Python desktop application, a static web version for browser-based usage, and an Android project for mobile extension. The overall system demonstrates the practical integration of cryptography, image processing, user interface design, and software deployment in one complete solution.

---

## Introduction

In the modern digital world, secure communication has become increasingly important. Users frequently share confidential files, personal information, and sensitive documents over digital channels. While encryption can protect the contents of such data, encrypted files often appear suspicious because it is obvious that protected information is being transmitted.

Steganography addresses this limitation by hiding secret information inside an ordinary digital object such as an image, audio file, or video. Among these media, images are commonly used because they are easy to share and contain enough pixel data to hide information without causing obvious visual changes. However, basic steganography alone is not sufficient, because if an attacker discovers the hidden bits, the secret message may still be exposed.

The Secure Steganography System combines steganography and cryptography into a single workflow. Before embedding, the payload is encrypted. After encryption, the ciphertext is hidden inside an image using randomized bit placement. As a result, the project provides two layers of protection: concealment of the message and security of the concealed content.

This project is valuable as both an academic and practical system because it demonstrates secure design principles, password-based authentication, image-based data hiding, software packaging, and cross-platform deployment.

---

## Problem Statement

During digital communication, sensitive information may be intercepted, monitored, or modified by unauthorized parties. Although encryption can make data unreadable, encrypted files still reveal that secret communication is taking place. This can attract suspicion or targeted attacks.

A secure solution is therefore needed that not only protects the content of the data but also hides its presence. Existing simple steganography methods often suffer from weak security because they embed data without proper encryption, predictable storage patterns, or authentication checks.

The problem addressed in this project is the need for a user-friendly system that can:

1. Hide text or file data inside an image.
2. Protect the hidden data using strong encryption.
3. Prevent unauthorized extraction without the correct password.
4. Detect tampering or incorrect passwords during recovery.
5. Work in practical desktop and web environments.

---

## Objectives

The major objective of this project is to develop a secure and practical steganography application for hiding and recovering confidential data inside images.

The specific objectives are:

1. To hide text messages and files inside digital images.
2. To protect hidden content using AES-256-GCM encryption.
3. To derive secure keys from user passwords using PBKDF2-SHA256.
4. To use randomized embedding positions instead of simple sequential storage.
5. To reduce visible distortion by preferring higher-texture image regions.
6. To provide a user-friendly desktop interface and a browser-based web interface.
7. To support deployment and packaging for practical demonstration.

---

## Literature Review

Steganography is the science of concealing information inside another medium so that the existence of the information is hidden. One of the most common techniques is Least Significant Bit steganography, in which the lowest bit of image pixel values is modified to carry secret data. LSB-based approaches are simple and efficient, but purely sequential embedding may be easier to detect with statistical analysis.

Cryptography, on the other hand, focuses on protecting the contents of information. Modern authenticated encryption methods such as AES-GCM provide confidentiality as well as integrity verification. This means the hidden content remains unreadable without the correct key, and any unauthorized change can be detected during decryption.

Many research and educational projects show that combining steganography with encryption creates a more secure communication model than using either method alone. Password-based key derivation techniques such as PBKDF2 are also widely recommended because they strengthen user passwords against brute-force attacks. Based on these ideas, this project adopts a combined approach that includes encrypted payload packaging, randomized LSB embedding, password-based key derivation, and tamper-aware extraction.

---

## Methodology / Approach

The methodology of the Secure Steganography System follows a layered approach in which the payload is first prepared, then encrypted, and finally embedded inside the carrier image.

### 1. Payload Preparation

The system accepts either a text message or a file. The selected payload is converted into a package that stores:

- payload type
- original file name
- MIME type
- payload length
- actual payload bytes

This package structure helps the system restore the original content correctly during decoding.

### 2. Encryption

The packaged payload is encrypted before embedding. The system uses:

- AES-256-GCM for authenticated encryption
- PBKDF2-SHA256 with 250,000 iterations for key derivation
- a random 16-byte salt
- a random 12-byte nonce

This ensures that even if hidden data is extracted incorrectly, it cannot be read without the correct password.

### 3. Header Construction

The system stores a compact public header in the image. This header contains:

- format magic value
- version number
- encryption salt
- shuffle salt
- nonce
- ciphertext length

The header helps the decoder understand how to recover the hidden encrypted payload.

### 4. Randomized Embedding

Instead of embedding payload bits in a simple predictable order, the project derives a shuffle seed from the password and salt. The candidate pixel channels are ranked using texture information, and the encrypted bits are embedded into a shuffled set of higher-quality positions. This improves stealth compared with plain sequential LSB embedding.

### 5. Recovery Process

During decoding, the system:

1. reads the public header,
2. regenerates the same randomized positions,
3. extracts the ciphertext,
4. decrypts it using the password,
5. reconstructs the original text or file.

If the password is wrong or the image has been modified, authenticated decryption fails.

---

## System Design / Architecture

The project is designed as a modular system with separate layers for interface, processing, and storage.

### 1. User Interface Layer

This layer handles user interaction.

- `ui/app.py` provides the desktop graphical interface using Tkinter.
- `web/index.html`, `web/styles.css`, and `web/app.js` provide the browser-based interface.
- `android-app/` contains the Android extension of the project.

### 2. Processing Layer

This layer performs the core security and steganography operations.

- `encoder.py` prepares the image, builds the public header, selects pixel channels, and embeds encrypted bits.
- `decoder.py` reads the header, reconstructs embedding positions, extracts ciphertext, and recovers the original package.
- `encryption.py` manages key derivation, encryption, decryption, and shuffle-seed generation.
- `utils.py` supports payload packaging, logging, file handling, and output recovery.

### 3. Storage and Output Layer

This layer manages generated files and deployment artifacts.

- `output/` stores encoded images and recovered files.
- `logs/` stores operation logs.
- `dist/` contains packaged desktop builds.
- `scripts/` contains installer and packaging scripts.

### Architecture Flow

User Input -> Payload Packaging -> AES-256-GCM Encryption -> Public Header Generation -> Randomized LSB Embedding -> PNG Output  
PNG Input -> Header Extraction -> Randomized Position Regeneration -> Ciphertext Recovery -> Authenticated Decryption -> Original Payload Output

---

## Implementation

The implementation of the project is based on real working modules in the repository.

### Desktop Application

The desktop application is started from `main.py` and built around `ui/app.py`. It provides separate encode and decode workflows, password entry, output selection, progress updates, and result summaries. It also supports drag-and-drop when `tkinterdnd2` is available.

### Encoding Module

`encoder.py` performs the following operations:

1. loads the carrier image and converts it to RGBA format,
2. builds the payload bundle,
3. encrypts the bundle,
4. creates the public header,
5. calculates capacity,
6. ranks candidate channels by texture,
7. randomizes payload positions using a password-derived seed,
8. writes header bits and payload bits into image channels,
9. saves the output as PNG.

### Decoding Module

`decoder.py` performs the reverse process:

1. loads the stego image,
2. reads and validates the public header,
3. calculates the randomized positions,
4. extracts ciphertext bits,
5. decrypts the ciphertext,
6. parses the payload package,
7. restores text or file output.

### Encryption Module

`encryption.py` uses the `cryptography` library to implement:

- PBKDF2-SHA256 key derivation with 250,000 iterations
- AES-256-GCM encryption and decryption
- shuffle-seed derivation for randomized embedding

### Web Version

The `web/` folder contains a static browser implementation. The logic in `web/app.js` mirrors the desktop workflow: it loads the image in the browser, encrypts the package with Web Crypto, embeds the bits into a canvas image, and downloads a PNG output. The browser version also supports decoding and extracted-file download.

### Packaging and Deployment

The project includes:

- PyInstaller specifications for desktop executable generation
- Linux install and build scripts
- Debian package build support
- Windows setup build support
- Netlify-ready static hosting for the web application

---

## Results and Analysis

The implemented system successfully demonstrates secure image-based data hiding in a usable software form.

### Observed Results

1. Secret text can be hidden and recovered correctly from a carrier image.
2. Arbitrary files can be hidden and later extracted with their original metadata.
3. Incorrect passwords fail during authenticated decryption, preventing false recovery.
4. PNG output preserves hidden data reliably.
5. The randomized and texture-aware embedding approach reduces obvious visible distortion.
6. The same project concept works across desktop, web, and Android-oriented environments.

### Practical Evidence from the Project

The repository already includes generated outputs and packaged artifacts such as:

- encoded carrier output in `output/`
- extracted sample output in `output/`
- Linux and Windows packaged builds in `dist/`
- deployable web application in `web/`

### Analysis

The project achieves a balance between security, usability, and implementation simplicity.

- Encryption protects the payload even if hidden bits are discovered.
- Steganography reduces suspicion by hiding the presence of the message.
- Randomized embedding is stronger than naive sequential LSB placement.
- Texture-aware channel selection helps reduce visually noticeable changes.
- The dependency on PNG output is necessary to avoid lossy compression damage.

Overall, the results show that the project is suitable for academic demonstration as well as practical prototype use.

---

## Practical Demonstration

The system can be demonstrated in the following sequence:

### Encoding Demo

1. Open the desktop app or web app.
2. Select a carrier image.
3. Choose whether to hide text or a file.
4. Enter the secret message or select the file.
5. Enter a password.
6. Start encoding and save the PNG output image.

### Decoding Demo

1. Open the decode section.
2. Select the generated stego image.
3. Enter the same password.
4. Start decoding.
5. View the recovered text or save the extracted file.

### Key Demonstration Points

- Visual appearance of the output image remains nearly unchanged.
- Recovery works correctly only with the right password.
- Wrong password or modified content causes authentication failure.
- The project demonstrates both concealment and content protection.

---

## Challenges and Limitations

Although the system is effective, a number of practical limitations remain.

### Challenges Faced

1. Balancing payload capacity against image quality.
2. Preventing visible artifacts after data embedding.
3. Designing a secure but user-friendly workflow.
4. Supporting both desktop and browser-based implementations.
5. Ensuring extracted file recovery with correct metadata.

### Limitations

1. Large payloads require large carrier images.
2. The stego output must be saved as PNG because JPEG compression is lossy.
3. Security still depends partly on password quality.
4. Advanced forensic or statistical analysis may still detect modification patterns.
5. Browser-based file handling is more limited than desktop file handling.

---

## Future Scope

The project can be extended in several useful directions:

1. Add support for audio and video steganography.
2. Improve capacity estimation and image quality analytics.
3. Add cloud backup or secure sharing integration.
4. Introduce stronger anti-forensic embedding strategies.
5. Add multi-user or token-based authentication support.
6. Improve visualization, reporting, and usage analytics.
7. Extend the Android version into a complete production-ready mobile app.

---

## Conclusion

The Secure Steganography System is a complete and practical implementation of secure hidden communication. It combines the concealment power of steganography with the strength of authenticated encryption to protect text and file data inside ordinary-looking images.

The project demonstrates several important cybersecurity concepts, including password-based key derivation, AES-256-GCM encryption, randomized embedding, image processing, metadata packaging, and tamper-aware recovery. Its desktop, web, and packaging support also make it stronger than a purely theoretical or classroom-only project.

In conclusion, this project successfully fulfills its main goal of hiding and protecting secret information in a user-friendly and technically meaningful way. It is suitable for academic presentation, practical demonstration, and future enhancement.

---

## References

1. Python Software Foundation, Python Documentation.
2. Cryptography Project Documentation for AESGCM and PBKDF2.
3. NumPy Documentation for array and bit operations.
4. Pillow Documentation for image processing in Python.
5. Tkinter Documentation for desktop graphical user interface development.
6. PyInstaller Documentation for executable packaging.
7. Web Crypto API Documentation for browser-based encryption support.
8. Standard concepts of AES, PBKDF2, and Least Significant Bit steganography.
