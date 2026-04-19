# StegoTool Pro v1.0.1 Release Checklist

## Environment

- [ ] Fresh virtual environment created
- [ ] Runtime dependencies installed from `requirements.txt`
- [ ] Build dependencies installed from `build/requirements-build.txt`
- [ ] App launches with `python -m app.main`

## Encode Workflow

- [ ] Encode text payload into image carrier
- [ ] Encode file payload into image carrier
- [ ] Encode payload into audio carrier
- [ ] Encode payload into video carrier
- [ ] Encode primary payload with decoy payload
- [ ] Encode with integrity tag enabled
- [ ] Encode with technique hint enabled
- [ ] Output path selection works
- [ ] Encode result card shows success, metadata, and output path

## Decode Workflow

- [ ] Decode primary payload with primary password
- [ ] Decode decoy payload with decoy password
- [ ] Single-password decode workflow remains clear
- [ ] Auto technique decode works where applicable
- [ ] Explicit LSB decode works where applicable
- [ ] Explicit PVD decode works for supported image carriers
- [ ] Integrity tag verified for valid payload
- [ ] Integrity failure or missing integrity is presented clearly
- [ ] Save decoded action works
- [ ] Open folder action works
- [ ] Copy path action works

## Preview Checks

- [ ] Cover image preview renders
- [ ] Cover audio preview renders or shows fallback
- [ ] Cover video preview renders or shows fallback
- [ ] Selected stego file preview renders or shows fallback
- [ ] Decoded image output preview renders
- [ ] Decoded audio output preview renders or shows fallback
- [ ] Decoded video output preview renders or shows fallback
- [ ] Unsupported binary preview shows file info/fallback
- [ ] External-open fallback works for unavailable media previews

## UI Content

- [ ] Tutorial page opens
- [ ] Encode tutorial screenshots load
- [ ] Decode tutorial screenshots load
- [ ] About page opens
- [ ] Logo appears in expanded sidebar
- [ ] Logo appears in collapsed sidebar
- [ ] Sidebar navigation works for Encode, Decode, Tutorial, and About

## EXE Build

- [ ] `pyinstaller build\StegoToolPro.spec` completes
- [ ] `dist\StegoToolPro.exe` launches
- [ ] EXE opens the desktop window
- [ ] EXE starts the local API successfully
- [ ] EXE can encode and decode a small image payload
- [ ] EXE icon is correct
- [ ] File properties show version `1.0.1`

## Installer

- [ ] Inno Setup compiles `installer\stegotool.iss`
- [ ] Installer output is `StegoToolPro-Setup-1.0.1.exe`
- [ ] Installer installs into Program Files
- [ ] Start Menu shortcut launches the app
- [ ] Optional desktop shortcut launches the app
- [ ] Installed app can encode/decode a small payload
- [ ] Uninstaller removes the app
- [ ] Reinstall after uninstall works
