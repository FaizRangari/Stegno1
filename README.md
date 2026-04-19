# 🔐 StegoTool Pro

> Hide and extract data in images, audio, and video — securely and locally.

---

## 📌 Overview

StegoTool Pro is a desktop steganography application that enables users to embed and extract hidden data within media files using encryption and integrity verification.

Designed with a clean UI and guided workflow, it supports secure data concealment across multiple media formats.

---

## ✨ Features

- 🔒 Encode secret data into media files (image, audio, video)
- 🔓 Decode hidden data with integrity verification
- 🕵️ Decoy password support (plausible deniability)
- 🎬 Built-in preview for image, audio, and video
- 💻 Desktop application (no browser required)
- ⚡ Fully local processing (no external API)

---

## 🖼️ Screenshots

### Encode Workflow
![Payload](docs/screenshots/encode-payload.png)
![Carrier](docs/screenshots/encode-carrier.png)
![Passwords](docs/screenshots/encode-passwords.png)
![Result](docs/screenshots/encode-result.png)

### Decode Workflow
![Input](docs/screenshots/decode-input.png)
![Result](docs/screenshots/decode-result.png)

---

## 📦 Installation

👉 Download the latest version:

➡️ https://github.com/iJainamJain/StegoTool-Pro/releases

### Steps

1. Download `StegoToolPro-Setup-1.0.0.exe`
2. Run the installer
3. Launch from Start Menu or Desktop

---

## ⚙️ Tech Stack

- **Frontend:** HTML, CSS, JavaScript (PyWebView UI)
- **Backend:** Python (FastAPI)
- **Core:**
  - NumPy
  - PyCryptodome
  - Pillow
  - AV (video processing)

---

## 🔐 Security Notes

- All operations are performed locally
- No data is transmitted externally
- Supports encrypted payload handling
- Integrity verification ensures data correctness

---

## 📁 Project Structure


stego_app/
├── app/ # App launcher (PyWebView)
├── api/ # FastAPI endpoints
├── core/ # Steganography + crypto logic
├── ui/ # Frontend UI
├── assets/ # Icons, tutorial images
├── build/ # Packaging config
├── installer/ # Installer setup


---

## 👨‍💻 Developers

- Jainam Jain  
- Sahil Patil  
- Himanshu Shinde  
- Aditya Deshmukh  

**Vidyalankar Institute of Technology**

---

## 🚀 Version

**v1.0.0 — Initial stable release**

---

## ⭐ Feedback

If you try the app, feel free to share feedback or suggestions!