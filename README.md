# StegoTool Pro

StegoTool Pro is a local Windows desktop tool for hiding and extracting encrypted payloads inside supported media files. It combines a Python FastAPI backend, a PyWebView desktop shell, and a dark HTML/CSS/JavaScript interface.

## v1 Scope

- Encode and decode workflows
- Image, audio, and video carrier support
- Primary and decoy payload support
- Text and file payload support
- Integrity tag and technique hint options
- Local media preview for image, audio, and video files
- Tutorial and About pages
- Windows PyInstaller packaging readiness

## Project Structure

```text
stego_app/
  app/        Desktop launcher and PyWebView bridge
  api/        FastAPI routes and request schemas
  core/       Steganography, crypto, media, and utility logic
  ui/         HTML/CSS/JavaScript frontend
  assets/     Logo, icon, and tutorial screenshots
  build/      PyInstaller spec and version metadata
  installer/  Placeholder for future installer scripts
  docs/       Product and packaging notes
```

## Setup

```powershell
cd stego_app
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

```powershell
python -m app.main
```

The app starts a local FastAPI service on `127.0.0.1:8765` and opens the desktop WebView window.

## Build EXE

```powershell
pip install -r build\requirements-build.txt
pyinstaller build\StegoToolPro.spec
```

The spec bundles `ui/` and `assets/` so the WebView and branding assets resolve correctly in onefile builds.
