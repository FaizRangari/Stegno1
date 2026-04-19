import hashlib
import os
import random
import shutil
import struct
import tempfile
from pathlib import Path
from typing import Optional

import numpy as np


def bytes_to_bits_np(data: bytes) -> np.ndarray:
    return np.unpackbits(np.frombuffer(data, dtype=np.uint8))


def bits_np_to_bytes(bits: np.ndarray) -> bytes:
    n = (len(bits) // 8) * 8
    return np.packbits(bits[:n]).tobytes()


def get_shuffled_indices(max_index: int, password_str: str) -> list[int]:
    seed = hashlib.sha256(password_str.encode()).digest()
    rng = random.Random()
    rng.seed(seed)
    indices = list(range(max_index))
    rng.shuffle(indices)
    return indices


def read_payload_input(text: str, file_path: str, default_text: Optional[bytes], default_name: str):
    if file_path:
        with open(file_path, "rb") as f:
            return f.read(), os.path.basename(file_path)
    if text and text.strip():
        return text.encode("utf-8"), default_name
    if default_text is not None:
        return default_text, default_name
    raise ValueError("No secret data provided.")


def temp_output_path(filename: str) -> str:
    safe_name = Path(filename or "decoded.bin").name
    fd, path = tempfile.mkstemp(prefix="stegotool_", suffix="_" + safe_name)
    os.close(fd)
    return path


def write_temp_payload(data: bytes, filename: str) -> str:
    path = temp_output_path(filename)
    with open(path, "wb") as f:
        f.write(data)
    return path


def copy_file(src: str, dst: str) -> str:
    if not src:
        raise ValueError("Source file path is required.")
    if not dst:
        raise ValueError("Destination file path is required.")
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    return dst


def unpack_u64(data: bytes, offset: int = 0) -> int:
    return struct.unpack(">Q", data[offset : offset + 8])[0]
