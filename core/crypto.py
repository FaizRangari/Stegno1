import hashlib
import io
import zipfile
from typing import Optional, Tuple

from Crypto.Cipher import AES
from Crypto.Protocol.KDF import scrypt
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

MAGIC_LSB = b"\xFA\xCE\x01"
MAGIC_PVD = b"\xFA\xCE\x02"
MAGIC_LEN = 3
OUTER_CARRIER_KEY = "__STEGO_OUTER_ENVELOPE_V1__"


def sha256_digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encrypt(raw_data: bytes, password: bytes) -> bytes:
    salt = get_random_bytes(16)
    key = scrypt(password, salt, 32, N=2**14, r=8, p=1)
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return salt + iv + cipher.encrypt(pad(raw_data, AES.block_size))


def decrypt(full_blob: bytes, password: bytes) -> bytes:
    salt, iv = full_blob[:16], full_blob[16:32]
    key = scrypt(password, salt, 32, N=2**14, r=8, p=1)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(full_blob[32:]), AES.block_size)


def compress_data(data: bytes, filename: str = "secret_file") -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(filename, data)
    return buf.getvalue()


def decompress_data(blob: bytes) -> Tuple[bytes, str]:
    buf = io.BytesIO(blob)
    with zipfile.ZipFile(buf, "r") as zf:
        filename = zf.namelist()[0]
        return zf.read(filename), filename


def try_decrypt_payload(enc_blob: bytes, password: bytes):
    try:
        return decrypt(enc_blob, password), True
    except Exception:
        return None, False


def try_unpack_payload(decrypted_blob: Optional[bytes]):
    if decrypted_blob is None:
        return None
    try:
        if len(decrypted_blob) >= 64:
            potential_tag = decrypted_blob[-64:]
            try:
                tag_str = potential_tag.decode("ascii")
            except Exception:
                tag_str = None
            if tag_str is not None and all(c in "0123456789abcdef" for c in tag_str):
                compressed_part = decrypted_blob[:-64]
                try:
                    decoded, fname = decompress_data(compressed_part)
                    tag_ok = sha256_digest(decoded) == tag_str
                    if tag_ok:
                        return decoded, fname, True, True
                    return None
                except Exception:
                    pass
        try:
            decoded, fname = decompress_data(decrypted_blob)
            return decoded, fname, False, None
        except Exception:
            return None
    except Exception:
        return None
