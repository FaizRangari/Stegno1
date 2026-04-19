import os
import platform
import subprocess
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.decode import decode_job
from core.encode import encode_job
from core.utils import copy_file

from .schemas import DecodeRequest, EncodeRequest, OpenFolderRequest, SaveDecodedRequest

app = FastAPI(title="StegoTool Pro Local API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/encode")
def encode(req: EncodeRequest):
    try:
        payload = req.model_dump() if hasattr(req, "model_dump") else req.dict()
        result = encode_job(**payload)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/decode")
def decode(req: DecodeRequest):
    try:
        payload = req.model_dump() if hasattr(req, "model_dump") else req.dict()
        result = decode_job(**payload)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/open-folder")
def open_folder(req: OpenFolderRequest):
    try:
        target = Path(req.path)
        folder = target if target.is_dir() else target.parent
        if platform.system() == "Windows":
            os.startfile(str(folder))
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", str(folder)])
        else:
            subprocess.Popen(["xdg-open", str(folder)])
        return {"success": True, "path": str(folder)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/save-decoded")
def save_decoded(req: SaveDecodedRequest):
    try:
        output_path = copy_file(req.source_path, req.output_path)
        return {"success": True, "output_path": output_path}
    except Exception as e:
        return {"success": False, "error": str(e)}
