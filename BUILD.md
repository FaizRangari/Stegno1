# Build Guide

This guide prepares the v1.0.0 Windows desktop release for StegoTool Pro.

## 1. Create a Virtual Environment

Run from the `stego_app` directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

## 2. Install Runtime Dependencies

```powershell
pip install -r requirements.txt
```

## 3. Install Build Dependencies

```powershell
pip install -r build\requirements-build.txt
```

## 4. Build the EXE

Use the checked-in PyInstaller spec:

```powershell
pyinstaller build\StegoToolPro.spec
```

Expected output:

```text
dist\StegoToolPro.exe
```

The spec bundles:

- `ui/`
- `assets/`
- `assets/logo.ico`
- Windows version metadata from `build/version_info.txt`

## 5. Build the Installer

Install Inno Setup, then compile:

```powershell
iscc installer\stegotool.iss
```

Expected output:

```text
dist\installer\StegoToolPro-Setup-1.0.0.exe
```

## 6. Clean Build Artifacts

Before rebuilding a release candidate, remove old generated artifacts:

```powershell
Remove-Item -Recurse -Force build\StegoToolPro, dist
```

Then rebuild the EXE and installer.
