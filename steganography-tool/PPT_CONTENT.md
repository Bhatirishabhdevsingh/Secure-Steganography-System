# Secure Steganography System

## Slide 1: Title Slide

**Title:** Secure Steganography System  
**Subtitle:** Image-Based Secure Data Hiding Using Encryption  
**Presented By:** Rishabh dev Singh

---

## Slide 2: Introduction

- Secure communication is very important in the digital world.
- Normal encryption protects data, but it does not hide its presence.
- Steganography hides secret information inside another file like an image.
- This project combines **steganography + encryption** for better security.

**Short line to speak:**  
This project hides secret text or files inside images and protects them with password-based encryption.

---

## Slide 3: Problem Statement

- Sensitive data can be intercepted during transmission.
- Encrypted files are secure, but they still look suspicious.
- A better solution is needed to both **hide** and **secure** the data.
- This project solves that problem using image-based secure hiding.

---

## Slide 4: Objective of the Project

- To hide text or files inside an image.
- To secure hidden data using strong encryption.
- To allow extraction only with the correct password.
- To provide both desktop and web versions.
- To make the system simple and user-friendly.

---

## Slide 5: Technologies Used

**Programming Languages**
- Python
- JavaScript

**Frontend / UI**
- Tkinter
- HTML
- CSS

**Libraries**
- NumPy
- Pillow
- cryptography
- tkinterdnd2

**Packaging / Deployment**
- PyInstaller
- Debian package
- Inno Setup
- Netlify / Static Hosting

---

## Slide 6: Project Modules

- `main.py` -> starts the desktop app
- `ui/app.py` -> user interface
- `encoder.py` -> hides encrypted data inside image
- `decoder.py` -> extracts hidden data from image
- `encryption.py` -> encryption and decryption
- `utils.py` -> helper functions
- `web/` -> browser version

---

## Slide 7: Working of Encoding

1. User selects a carrier image.
2. User chooses text or file to hide.
3. User enters a password.
4. Data is packaged with metadata.
5. Data is encrypted using AES-256-GCM.
6. Encrypted bits are embedded into image pixels.
7. Output image is saved as PNG.

**Short line to speak:**  
In encoding, the system first encrypts the data and then hides it inside the image.

---

## Slide 8: Working of Decoding

1. User selects the stego image.
2. User enters the password.
3. System reads the hidden header.
4. Encrypted bits are extracted from randomized positions.
5. Data is decrypted using the password.
6. Original text or file is recovered.

**Short line to speak:**  
In decoding, the hidden encrypted data is extracted and then converted back into the original file or message.

---

## Slide 9: Security Features

- AES-256-GCM encryption
- PBKDF2-SHA256 key derivation
- Password-protected extraction
- Randomized LSB embedding
- Texture-aware pixel selection
- Tamper detection using authenticated decryption

---

## Slide 10: Key Features

- Hide text inside images
- Hide files inside images
- Secure output with password
- Desktop application support
- Web application support
- Linux and Windows setup support
- Extract and recover hidden files

---

## Slide 11: Advantages

- Better privacy and secure communication
- Hides the existence of secret data
- Strong encryption with easy usability
- Supports both file and text payloads
- Practical implementation of cybersecurity concepts

---

## Slide 12: Limitations

- Large files require large images
- Output should be PNG for safe recovery
- Weak passwords reduce security
- Advanced analysis tools may still detect modifications

---

## Slide 13: Future Scope

- Add audio/video steganography
- Improve UI and visual analytics
- Add cloud integration
- Add multi-user secure sharing
- Improve anti-forensic protection

---

## Slide 14: Conclusion

- Secure Steganography System is a combination of **steganography and cryptography**.
- It hides secret data inside images and protects it with encryption.
- It is useful for secure communication, learning, and cybersecurity demonstration.
- The project is practical, user-friendly, and deployable.

**Closing line:**  
This project shows how hidden communication can be made safer with the help of encryption and image processing.

---

## Slide 15: Thank You

**Thank You**  
Any Questions?

