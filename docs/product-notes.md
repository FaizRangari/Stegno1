# Product Notes

## Product Boundary

StegoTool Pro v1 is local-only desktop software. It does not include cloud storage, browser deployment, multi-user accounts, remote APIs, or advanced steganalysis.

## Runtime

- Local FastAPI backend
- PyWebView desktop shell
- Plain HTML/CSS/JavaScript frontend
- PyInstaller-ready Windows build configuration

## Security Model

- Payload encryption uses the copied core crypto implementation.
- Primary and decoy payload behavior is preserved from the working prototype.
- Decode remains a single-password workflow.
- Carrier extraction and inner payload decryption remain separate stages.

## Packaging Notes

Build from the `stego_app` directory with:

```powershell
pyinstaller build\StegoToolPro.spec
```

Keep `ui/` and `assets/` bundled as data folders. The app launcher resolves these paths through `sys._MEIPASS` when frozen.
