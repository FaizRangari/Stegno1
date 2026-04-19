# 🔐 StegoTool Pro

<p align="center">
  <img src="assets/logo.png" alt="StegoTool Pro Logo" width="120">
</p>

<p align="center">
  <strong>Hide and extract data in images, audio, and video — securely and locally.</strong>
</p>

<p align="center">
  <a href="https://github.com/iJainamJain/StegoTool-Pro/releases/tag/v1.0.0">
    <img src="https://img.shields.io/badge/Release-v1.0.0-6f6ad9?style=for-the-badge" alt="Release v1.0.0">
  </a>
  <a href="https://github.com/iJainamJain/StegoTool-Pro/releases/download/v1.0.0/StegoToolPro-Setup-1.0.0.exe">
    <img src="https://img.shields.io/badge/Download-Installer-19d3c5?style=for-the-badge" alt="Download Installer">
  </a>
</p>

---

## 📌 Overview

StegoTool Pro is a desktop steganography application that allows users to securely embed and extract hidden data within image, audio, and video files.

It combines a modern desktop UI with local processing, encryption support, media preview, and guided workflows for both encoding and decoding.

---

## ✨ Features

- 🔒 Encode secret data into media files  
- 🔓 Decode hidden data with integrity verification  
- 🕵️ Decoy password support for plausible deniability  
- 🎬 Built-in preview for image, audio, and video  
- 💻 Desktop application with guided workflow  
- ⚡ Fully local processing with no external API dependency  
- 📘 Tutorial page for first-time users  

---

## 📦 Download

<p align="center">
  <a href="https://github.com/iJainamJain/StegoTool-Pro/releases/download/v1.0.0/StegoToolPro-Setup-1.0.0.exe">
    <img src="https://img.shields.io/badge/Download%20StegoTool%20Pro%20Installer-v1.0.0-19d3c5?style=for-the-badge" alt="Download StegoTool Pro Installer">
  </a>
</p>

### Installation

1. Download the installer  
2. Run `StegoToolPro-Setup-1.0.0.exe`  
3. Complete installation  
4. Launch from Start Menu or Desktop  

> ⚠️ Windows may show a SmartScreen warning because the app is not code-signed yet.  
> Click **More info → Run anyway**.

---

## 🖼️ Screenshots

### Encode Workflow

<p align="center">
  <img src="docs/screenshots/encode-payload.png" width="900"><br><br>
  <img src="docs/screenshots/encode-carrier.png" width="900"><br><br>
  <img src="docs/screenshots/encode-passwords.png" width="900"><br><br>
  <img src="docs/screenshots/encode-result.png" width="900">
</p>

### Decode Workflow

<p align="center">
  <img src="docs/screenshots/decode-input.png" width="900"><br><br>
  <img src="docs/screenshots/decode-result.png" width="900">
</p>

---

## ⚙️ Tech Stack

- **Frontend:** HTML, CSS, JavaScript  
- **Desktop Shell:** PyWebView  
- **Backend:** FastAPI  

**Core Libraries:**
- NumPy  
- PyCryptodome  
- Pillow  
- AV  

---

## 🔐 Security Notes

- All processing is performed locally  
- No data is sent to external services  
- Supports encrypted payload handling  
- Integrity verification ensures correctness of decoded output  

---

## 📁 Project Structure

```text
stego_app/
├── app/        # App launcher
├── api/        # FastAPI endpoints and schemas
├── core/       # Steganography and crypto logic
├── ui/         # Frontend UI
├── assets/     # Icons and tutorial images
├── docs/       # Notes and screenshots
├── installer/  # Inno Setup installer files
├── build/      # Build configuration

```

---

## 👨‍💻 Developers

- Jainam Jain (Lead)
- Sahil Patil
- Himanshu Shinde
- Aditya Deshmukh

Vidyalankar Institute of Technology

---

## 🚀 Version

- v1.0.0 — Initial stable release

---

## ⭐ Feedback

- If you try the app, feel free to share feedback, issues, or suggestions through the GitHub repository.