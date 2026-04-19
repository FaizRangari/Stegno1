import os
import struct
from pathlib import Path

from .crypto import MAGIC_LSB, MAGIC_PVD, OUTER_CARRIER_KEY, compress_data, encrypt, sha256_digest
from .media import encode_media, save_stego_object
from .models import EncodeOptions
from .utils import read_payload_input


def encode_job(
    secret_text: str = "",
    secret_file_path: str = "",
    decoy_text: str = "",
    decoy_file_path: str = "",
    cover_media_path: str = "",
    technique: str = "LSB",
    primary_password: str = "",
    decoy_password: str = "",
    use_integrity: bool = True,
    use_hint: bool = True,
    output_path: str = "",
    progress_cb=None,
) -> dict:
    opts = EncodeOptions(
        secret_text=secret_text,
        secret_file_path=secret_file_path,
        decoy_text=decoy_text,
        decoy_file_path=decoy_file_path,
        cover_media_path=cover_media_path,
        technique=(technique or "LSB").upper(),
        primary_password=primary_password,
        decoy_password=decoy_password,
        use_integrity=use_integrity,
        use_hint=use_hint,
        output_path=output_path,
    )
    if not opts.cover_media_path:
        raise ValueError("Cover media path is required.")
    if not os.path.exists(opts.cover_media_path):
        raise FileNotFoundError(f"Cover media not found: {opts.cover_media_path}")
    if not opts.primary_password:
        raise ValueError("Primary password cannot be empty.")
    if opts.technique not in ("LSB", "PVD"):
        raise ValueError("Technique must be LSB or PVD.")
    if not opts.output_path:
        ext = ".mkv" if Path(opts.cover_media_path).suffix.lower() in (".mkv", ".mov", ".avi", ".mp4") else Path(opts.cover_media_path).suffix
        opts.output_path = str(Path(opts.cover_media_path).with_name(Path(opts.cover_media_path).stem + "_stego" + ext))

    secret_raw, secret_name = read_payload_input(opts.secret_text, opts.secret_file_path, None, "secret.txt")
    decoy_raw, decoy_name = read_payload_input(opts.decoy_text, opts.decoy_file_path, b"Harmless decoy file.", "decoy.txt")

    password = opts.primary_password.encode()
    decoy_pw = (opts.decoy_password or opts.primary_password).encode()
    compressed_secret = compress_data(secret_raw, secret_name)
    integrity_tag = sha256_digest(secret_raw).encode("ascii") if opts.use_integrity else b""
    enc_secret = encrypt(compressed_secret + integrity_tag, password)
    enc_decoy = encrypt(compress_data(decoy_raw, decoy_name), decoy_pw)

    main_payload = struct.pack(">Q", len(enc_secret)) + enc_secret + struct.pack(">Q", len(enc_decoy)) + enc_decoy
    if opts.use_hint:
        main_payload = (MAGIC_LSB if opts.technique == "LSB" else MAGIC_PVD) + main_payload

    if progress_cb:
        progress_cb(0.08)
    stego_obj, error = encode_media(
        opts.cover_media_path,
        main_payload,
        opts.technique,
        OUTER_CARRIER_KEY,
        progress_cb=lambda f: progress_cb(0.10 + f * 0.78) if progress_cb else None,
    )
    if error:
        raise RuntimeError(error)
    final_output = save_stego_object(
        opts.cover_media_path,
        opts.output_path,
        stego_obj,
        progress_cb=lambda f: progress_cb(0.90 + f * 0.10) if progress_cb else None,
    )
    if progress_cb:
        progress_cb(1.0)
    return {
        "success": True,
        "output_path": final_output,
        "technique": opts.technique,
        "cover_media_path": opts.cover_media_path,
        "secret_filename": secret_name,
        "decoy_filename": decoy_name,
        "secret_size": len(secret_raw),
        "decoy_size": len(decoy_raw),
        "embedded_bytes": len(main_payload),
        "sha256": sha256_digest(secret_raw),
        "integrity": opts.use_integrity,
        "hint": opts.use_hint,
    }
