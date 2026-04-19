import os
import struct

from .crypto import MAGIC_LEN, MAGIC_LSB, MAGIC_PVD, OUTER_CARRIER_KEY, sha256_digest, try_decrypt_payload, try_unpack_payload
from .media import AV_AVAILABLE, audio_bit_extractor, decode_media, lsb_bit_extractor_image, video_bit_extractor
from .models import DecodeOptions
from .utils import write_temp_payload


def _detect_hint(media_path: str, password_str: str):
    ext = os.path.splitext(media_path)[1].lower()
    try:
        if ext in (".png", ".bmp"):
            bit_gen = lsb_bit_extractor_image(media_path, password_str)
        elif ext == ".wav":
            bit_gen = audio_bit_extractor(media_path, password_str)
        elif ext in (".mkv", ".mov", ".avi", ".mp4") and AV_AVAILABLE:
            bit_gen = video_bit_extractor(media_path, password_str)
        else:
            return None
        header_bits = "".join(next(bit_gen) for _ in range(64))
        if struct.unpack(">Q", int(header_bits, 2).to_bytes(8, "big"))[0] == 0:
            return None
        hint_bits = "".join(next(bit_gen) for _ in range(MAGIC_LEN * 8))
        return int(hint_bits, 2).to_bytes(MAGIC_LEN, "big")
    except Exception:
        return None


def _choose_technique(media_path: str, chosen_technique: str, entered_password: str):
    chosen = (chosen_technique or "Auto").upper()
    if chosen in ("LSB", "PVD"):
        return chosen, OUTER_CARRIER_KEY, None
    hint = _detect_hint(media_path, OUTER_CARRIER_KEY)
    carrier_key = OUTER_CARRIER_KEY
    legacy_used = False
    if hint not in (MAGIC_LSB, MAGIC_PVD):
        hint_legacy = _detect_hint(media_path, entered_password)
        if hint_legacy in (MAGIC_LSB, MAGIC_PVD):
            hint = hint_legacy
            carrier_key = entered_password
            legacy_used = True
    if hint == MAGIC_LSB:
        return "LSB", carrier_key, legacy_used
    if hint == MAGIC_PVD:
        return "PVD", carrier_key, legacy_used
    return "LSB", carrier_key, legacy_used


def _parse_envelope(hidden_blob: bytes):
    hint_found = hidden_blob.startswith(MAGIC_LSB) or hidden_blob.startswith(MAGIC_PVD)
    data_payload = hidden_blob[MAGIC_LEN:] if hint_found else hidden_blob
    real_len = struct.unpack(">Q", data_payload[:8])[0]
    enc_real = data_payload[8 : 8 + real_len]
    decoy_start = 8 + real_len
    decoy_len = struct.unpack(">Q", data_payload[decoy_start : decoy_start + 8])[0]
    enc_decoy = data_payload[decoy_start + 8 : decoy_start + 8 + decoy_len]
    return enc_real, enc_decoy, hint_found


def decode_job(stego_file_path: str = "", password: str = "", technique: str = "Auto", output_dir: str | None = None, progress_cb=None) -> dict:
    opts = DecodeOptions(stego_file_path=stego_file_path, password=password, technique=technique, output_dir=output_dir)
    if not opts.stego_file_path:
        raise ValueError("Stego file path is required.")
    if not os.path.exists(opts.stego_file_path):
        raise FileNotFoundError(f"Stego file not found: {opts.stego_file_path}")
    if not opts.password:
        raise ValueError("Password cannot be empty.")

    selected_technique, carrier_key, legacy_used = _choose_technique(opts.stego_file_path, opts.technique, opts.password)
    if progress_cb:
        progress_cb(0.10)
    hidden_blob, error = decode_media(
        opts.stego_file_path,
        selected_technique,
        carrier_key,
        progress_cb=lambda f: progress_cb(0.10 + f * 0.70) if progress_cb else None,
    )
    if error and carrier_key == OUTER_CARRIER_KEY:
        hidden_blob_legacy, error_legacy = decode_media(
            opts.stego_file_path,
            selected_technique,
            opts.password,
            progress_cb=lambda f: progress_cb(0.10 + f * 0.70) if progress_cb else None,
        )
        if not error_legacy and hidden_blob_legacy:
            hidden_blob = hidden_blob_legacy
            error = None
            legacy_used = True
    if error:
        raise RuntimeError(f"Stage 1 failed - could not extract data from carrier. Cause: {error}")

    try:
        enc_real, enc_decoy, hint_found = _parse_envelope(hidden_blob)
    except Exception as e:
        raise RuntimeError(f"Stage 2 failed - payload envelope is corrupt. Cause: {e}") from e

    if progress_cb:
        progress_cb(0.90)
    password_bytes = opts.password.encode()
    decrypted_real, real_ok = try_decrypt_payload(enc_real, password_bytes)
    real_result = try_unpack_payload(decrypted_real) if real_ok else None
    label = "primary"
    result = real_result
    if result is None:
        decrypted_decoy, decoy_ok = try_decrypt_payload(enc_decoy, password_bytes)
        result = try_unpack_payload(decrypted_decoy) if decoy_ok else None
        label = "decoy"
    if result is None:
        raise ValueError("Stage 3 failed - invalid password or corrupted data.")

    decoded_data, filename, tag_found, tag_ok = result
    if label == "decoy":
        tag_found = False
        tag_ok = None
    temp_path = write_temp_payload(decoded_data, filename)
    try:
        text_preview = decoded_data.decode("utf-8")[:4000]
        is_text = True
    except UnicodeDecodeError:
        text_preview = ""
        is_text = False
    if progress_cb:
        progress_cb(1.0)
    return {
        "success": True,
        "payload_label": label,
        "filename": filename,
        "size": len(decoded_data),
        "sha256": sha256_digest(decoded_data),
        "text_preview": text_preview,
        "is_text": is_text,
        "decoded_temp_path": temp_path,
        "technique": selected_technique,
        "hint_found": hint_found,
        "legacy_carrier": bool(legacy_used),
        "integrity_tag_found": bool(tag_found),
        "integrity_ok": tag_ok,
    }
