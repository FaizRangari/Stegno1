import mimetypes
import os
from pathlib import Path
import platform
import subprocess
import sys
import threading
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn
import webview

from api.server import app as fastapi_app

HOST = "127.0.0.1"
PORT = 8765

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = PROJECT_ROOT

UI_PATH = BASE_DIR / "ui" / "index.html"


def run_api():
    config = uvicorn.Config(fastapi_app, host=HOST, port=PORT, log_level="warning")
    server = uvicorn.Server(config)
    server.run()


class DialogBridge:
    def open_file(self, file_types=None):
        window = webview.windows[0]
        result = window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=tuple(file_types or ("All files (*.*)",)),
        )
        return result[0] if result else ""

    def save_file(self, filename=""):
        window = webview.windows[0]
        result = window.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename=filename or "",
            file_types=("All files (*.*)",),
        )
        return result if isinstance(result, str) else (result[0] if result else "")

    def file_preview(self, path=""):
        target = Path(path or "")
        if not target.exists() or not target.is_file():
            return {"exists": False, "error": "File not found."}

        ext = target.suffix.lower()
        mime, _ = mimetypes.guess_type(str(target))
        image_exts = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
        audio_exts = {".wav", ".mp3", ".ogg", ".flac", ".m4a"}
        video_exts = {".mp4", ".webm", ".mov", ".avi", ".mkv"}
        text_exts = {
            ".txt", ".md", ".csv", ".json", ".xml", ".html", ".css", ".js",
            ".py", ".log", ".ini", ".toml", ".yaml", ".yml",
        }

        kind = "binary"
        if ext in image_exts or (mime or "").startswith("image/"):
            kind = "image"
        elif ext in audio_exts or (mime or "").startswith("audio/"):
            kind = "audio"
        elif ext in video_exts or (mime or "").startswith("video/"):
            kind = "video"
        elif ext in text_exts or (mime or "").startswith("text/"):
            kind = "text"

        data = {
            "exists": True,
            "name": target.name,
            "path": str(target),
            "uri": target.resolve().as_uri(),
            "extension": ext,
            "mime": mime or "application/octet-stream",
            "kind": kind,
            "size": target.stat().st_size,
        }
        if kind == "text":
            try:
                data["text"] = target.read_text(encoding="utf-8", errors="replace")[:8000]
            except Exception:
                data["kind"] = "binary"
                data["text"] = ""
        return data

    def open_external(self, path=""):
        target = Path(path or "")
        if not target.exists():
            return {"success": False, "error": "File not found."}
        try:
            if platform.system() == "Windows":
                os.startfile(str(target))
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", str(target)])
            else:
                subprocess.Popen(["xdg-open", str(target)])
            return {"success": True}
        except Exception as exc:
            return {"success": False, "error": str(exc)}


def main():
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    time.sleep(0.8)
    webview.create_window(
        "StegoTool Pro",
        str(UI_PATH),
        js_api=DialogBridge(),
        width=1200,
        height=800,
        min_size=(980, 680),
    )
    webview.start(debug=False)


if __name__ == "__main__":
    main()
