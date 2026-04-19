import gc
import math
import os
import struct
import wave
from concurrent.futures import ThreadPoolExecutor, as_completed
from fractions import Fraction

import numpy as np
from PIL import Image

from .utils import bytes_to_bits_np, get_shuffled_indices

try:
    import av

    AV_AVAILABLE = True
except ImportError:
    av = None
    AV_AVAILABLE = False

VIDEO_CHUNK_FRAMES = 200
PVD_RANGES = [(0, 7, 3), (8, 15, 3), (16, 31, 4), (32, 63, 5), (64, 127, 6), (128, 255, 7)]


def encode_lsb_image(image_path: str, secret_data: bytes, password_str: str):
    try:
        img = Image.open(image_path).convert("RGB")
    except Exception as e:
        return None, f"Could not open image: {e}"
    arr = np.array(img)
    height, width = arr.shape[:2]
    bits = bytes_to_bits_np(struct.pack(">Q", len(secret_data)) + secret_data)
    if len(bits) > width * height * 3:
        return None, "Secret data is too large for this image with LSB."
    flat = arr.reshape(-1, 3)
    bit_idx = 0
    for pid in get_shuffled_indices(len(flat), password_str):
        if bit_idx >= len(bits):
            break
        for ch in range(3):
            if bit_idx >= len(bits):
                break
            flat[pid, ch] = (flat[pid, ch] & 0xFE) | int(bits[bit_idx])
            bit_idx += 1
    result = Image.fromarray(arr)
    del arr, flat, bits
    return result, None


def lsb_bit_extractor_image(image_path: str, password_str: str):
    try:
        img = Image.open(image_path).convert("RGB")
        arr = np.array(img)
        flat = arr.reshape(-1, 3)
        for pid in get_shuffled_indices(len(flat), password_str):
            yield str(flat[pid, 0] & 1)
            yield str(flat[pid, 1] & 1)
            yield str(flat[pid, 2] & 1)
        del arr, flat
    except Exception:
        return


def decode_lsb_image(image_path: str, password_str: str):
    bit_gen = lsb_bit_extractor_image(image_path, password_str)
    try:
        header_bits = "".join(next(bit_gen) for _ in range(64))
        payload_len = struct.unpack(">Q", int(header_bits, 2).to_bytes(8, "big"))[0]
        if payload_len > 500 * 1024 * 1024:
            return None, "Payload length exceeds safety limit - wrong password?"
        payload_bits = "".join(next(bit_gen) for _ in range(payload_len * 8))
        return bytes(int(payload_bits[i : i + 8], 2) for i in range(0, len(payload_bits), 8)), None
    except (StopIteration, struct.error, ValueError) as e:
        return None, f"LSB image decode failed: {e}"


def get_pvd_range(diff: int):
    for r in PVD_RANGES:
        if r[0] <= diff <= r[1]:
            return r
    return None


def get_pvd_pair_coords(h: int, w: int, password_str: str) -> list:
    pairs = [(i, j) for i in range(h) for j in range(0, w - (w % 2), 2)]
    import hashlib
    import random

    rng = random.Random(hashlib.sha256(f"pvd_pairs_{password_str}".encode()).digest())
    rng.shuffle(pairs)
    return pairs


def _pvd_adjust_pair(p1: int, p2: int, new_diff: int):
    diff = abs(p1 - p2)
    m = new_diff - diff
    sign = 1 if p1 >= p2 else -1
    p1n = p1 + sign * math.ceil(m / 2)
    p2n = p2 - sign * math.floor(m / 2)
    if p1n < 0 or p2n < 0:
        shift = max(-p1n, -p2n)
        p1n += shift
        p2n += shift
    if p1n > 255 or p2n > 255:
        shift = max(p1n - 255, p2n - 255)
        p1n -= shift
        p2n -= shift
    return p1n, p2n


def encode_pvd_image(image_path: str, secret_data: bytes, password_str: str):
    try:
        img = Image.open(image_path).convert("L")
    except Exception as e:
        return None, f"Could not open image for PVD: {e}"
    pixels = np.array(img, dtype=int)
    h, w = pixels.shape
    bit_str = "".join(format(b, "08b") for b in secret_data)
    full_bits = format(len(bit_str), "064b") + bit_str
    data_idx = 0
    for i, j in get_pvd_pair_coords(h, w, password_str):
        if data_idx >= len(full_bits):
            break
        p1, p2 = int(pixels[i, j]), int(pixels[i, j + 1])
        pvd_range = get_pvd_range(abs(p1 - p2))
        if not pvd_range:
            continue
        lower, _, k = pvd_range
        remaining = len(full_bits) - data_idx
        k_use = min(k, remaining)
        bits = full_bits[data_idx : data_idx + k_use].ljust(k, "0")
        pixels[i, j], pixels[i, j + 1] = _pvd_adjust_pair(p1, p2, lower + int(bits, 2))
        data_idx += k_use
    if data_idx < len(full_bits):
        return None, "Data is too large for PVD on this image."
    result = Image.fromarray(pixels.astype(np.uint8))
    del pixels
    return result, None


def decode_pvd_image(image_path: str, password_str: str):
    try:
        img = Image.open(image_path).convert("L")
    except Exception as e:
        return None, f"Could not open stego image for PVD: {e}"
    pixels = np.array(img, dtype=int)
    h, w = pixels.shape
    all_bits = ""
    for i, j in get_pvd_pair_coords(h, w, password_str):
        diff = abs(int(pixels[i, j]) - int(pixels[i, j + 1]))
        pvd_range = get_pvd_range(diff)
        if not pvd_range:
            continue
        lower, _, k = pvd_range
        all_bits += format(diff - lower, f"0{k}b")
    del pixels
    if len(all_bits) < 64:
        return None, "Not enough bits for PVD length header."
    bit_count = struct.unpack(">Q", int(all_bits[:64], 2).to_bytes(8, "big"))[0]
    data_bits = all_bits[64 : 64 + bit_count]
    return bytes(int(data_bits[i : i + 8], 2) for i in range(0, len(data_bits), 8) if i + 8 <= len(data_bits)), None


def encode_audio(audio_path: str, secret_data: bytes, password_str: str):
    try:
        with wave.open(audio_path, "rb") as wav:
            params = wav.getparams()
            frames = bytearray(wav.readframes(wav.getnframes()))
    except Exception as e:
        return None, f"Could not read WAV: {e}"
    bits = bytes_to_bits_np(struct.pack(">Q", len(secret_data)) + secret_data)
    if len(bits) > len(frames):
        return None, "Secret data is too large for this WAV file."
    byte_indices = get_shuffled_indices(len(frames), password_str)
    for i, bit in enumerate(bits):
        frames[byte_indices[i]] = (frames[byte_indices[i]] & 0xFE) | int(bit)
    return (bytes(frames), params), None


def audio_bit_extractor(audio_path: str, password_str: str):
    try:
        with wave.open(audio_path, "rb") as wav:
            frames = wav.readframes(wav.getnframes())
        for byte_idx in get_shuffled_indices(len(frames), password_str):
            yield str(frames[byte_idx] & 1)
    except Exception:
        return


def decode_audio(audio_path: str, password_str: str):
    bit_gen = audio_bit_extractor(audio_path, password_str)
    try:
        header_bits = "".join(next(bit_gen) for _ in range(64))
        payload_len = struct.unpack(">Q", int(header_bits, 2).to_bytes(8, "big"))[0]
        if payload_len > 500 * 1024 * 1024:
            return None, "Payload size exceeds safety limit - wrong password?"
        payload_bits = "".join(next(bit_gen) for _ in range(payload_len * 8))
        return bytes(int(payload_bits[i : i + 8], 2) for i in range(0, len(payload_bits), 8)), None
    except (StopIteration, struct.error, ValueError) as e:
        return None, f"Audio decode failed: {e}"


def get_video_info(video_path: str) -> dict:
    if not AV_AVAILABLE:
        raise RuntimeError("PyAV not installed. Run: pip install av")
    with av.open(video_path) as container:
        stream = container.streams.video[0]
        frame_count = stream.frames
        if frame_count == 0:
            frame_count = sum(1 for _ in container.decode(video=0))
        rate = stream.average_rate or stream.base_rate or getattr(stream, "guessed_rate", None)
        return {
            "width": stream.width,
            "height": stream.height,
            "frames": frame_count,
            "rate": rate,
            "time_base": stream.time_base,
        }


def _embed_bits_in_frame(frame_arr: np.ndarray, frame_idx: int, binary_payload: str, start_bit: int, password_str: str):
    arr = frame_arr.copy()
    pixels = arr.reshape(-1, 3)
    h, w = arr.shape[:2]
    perm = get_shuffled_indices(w * h, f"{password_str}_{frame_idx}")
    data_idx = start_bit
    for pid in perm:
        if data_idx >= len(binary_payload):
            break
        for ch in range(3):
            if data_idx >= len(binary_payload):
                break
            pixels[pid, ch] = np.uint8((int(pixels[pid, ch]) & 0xFE) | int(binary_payload[data_idx]))
            data_idx += 1
    return frame_idx, arr, data_idx - start_bit


def _extract_bits_from_frame(frame_arr: np.ndarray, frame_idx: int, password_str: str):
    pixels = frame_arr.reshape(-1, 3)
    h, w = frame_arr.shape[:2]
    perm = get_shuffled_indices(w * h, f"{password_str}_{frame_idx}")
    bits = []
    for pid in perm:
        bits.append(str(pixels[pid, 0] & 1))
        bits.append(str(pixels[pid, 1] & 1))
        bits.append(str(pixels[pid, 2] & 1))
    return frame_idx, bits


def encode_video(video_path: str, secret_data: bytes, password_str: str, progress_cb=None):
    if not AV_AVAILABLE:
        return None, "PyAV not installed. Run: pip install av"
    try:
        info = get_video_info(video_path)
    except Exception as e:
        return None, f"Cannot read video info: {e}"
    width, height, total_frames = info["width"], info["height"], info["frames"]
    bits_per_frame = width * height * 3
    payload_bytes = struct.pack(">Q", len(secret_data)) + secret_data
    binary_payload = "".join(format(b, "08b") for b in payload_bytes)
    if len(binary_payload) > total_frames * bits_per_frame:
        return None, "Secret data is too large for this video."
    frame_order = get_shuffled_indices(total_frames, password_str)
    frame_bit_starts = {}
    consumed = 0
    for fi in frame_order:
        if consumed >= len(binary_payload):
            break
        frame_bit_starts[fi] = consumed
        consumed += bits_per_frame
    modified_frames = {}
    frames_processed = 0
    with av.open(video_path) as container:
        chunk = []
        for abs_idx, frame in enumerate(container.decode(video=0)):
            chunk.append((abs_idx, frame.to_ndarray(format="rgb24")))
            if len(chunk) >= VIDEO_CHUNK_FRAMES:
                _process_encode_chunk(chunk, frame_bit_starts, binary_payload, password_str, modified_frames)
                frames_processed += len(chunk)
                if progress_cb:
                    progress_cb(frames_processed / total_frames)
                chunk.clear()
                gc.collect()
        if chunk:
            _process_encode_chunk(chunk, frame_bit_starts, binary_payload, password_str, modified_frames)
            gc.collect()
    if progress_cb:
        progress_cb(1.0)
    return (info, modified_frames), None


def _process_encode_chunk(chunk, frame_bit_starts, binary_payload, password_str, modified_frames):
    with ThreadPoolExecutor() as executor:
        futures = {}
        for abs_idx, arr in chunk:
            if abs_idx in frame_bit_starts:
                futures[executor.submit(_embed_bits_in_frame, arr, abs_idx, binary_payload, frame_bit_starts[abs_idx], password_str)] = abs_idx
        for future in as_completed(futures):
            fi, arr, _ = future.result()
            modified_frames[fi] = arr


def video_bit_extractor(video_path: str, password_str: str):
    if not AV_AVAILABLE:
        return
    try:
        info = get_video_info(video_path)
        total_frames = info["frames"]
        frame_order = get_shuffled_indices(total_frames, password_str)
        frame_order_set = set(frame_order)
        frame_bits_buffer = {}
        with av.open(video_path) as container:
            chunk = []
            for abs_idx, frame in enumerate(container.decode(video=0)):
                if abs_idx in frame_order_set:
                    chunk.append((abs_idx, frame.to_ndarray(format="rgb24")))
                if len(chunk) >= VIDEO_CHUNK_FRAMES:
                    _process_extract_chunk(chunk, password_str, frame_bits_buffer)
                    chunk.clear()
                    gc.collect()
            if chunk:
                _process_extract_chunk(chunk, password_str, frame_bits_buffer)
                gc.collect()
        for fi in frame_order:
            if fi in frame_bits_buffer:
                yield from frame_bits_buffer[fi]
    except Exception:
        return


def _process_extract_chunk(chunk, password_str, frame_bits_buffer):
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(_extract_bits_from_frame, arr, abs_idx, password_str): abs_idx for abs_idx, arr in chunk}
        for future in as_completed(futures):
            fi, bits = future.result()
            frame_bits_buffer[fi] = bits


def decode_video(video_path: str, password_str: str, progress_cb=None):
    bit_gen = video_bit_extractor(video_path, password_str)
    try:
        header_bits = "".join(next(bit_gen) for _ in range(64))
        payload_len = struct.unpack(">Q", int(header_bits, 2).to_bytes(8, "big"))[0]
        if payload_len > 2 * 1024 * 1024 * 1024:
            return None, "Payload size exceeds safety limit - wrong password?"
        payload_bits = "".join(next(bit_gen) for _ in range(payload_len * 8))
        return bytes(int(payload_bits[i : i + 8], 2) for i in range(0, len(payload_bits), 8)), None
    except (StopIteration, struct.error, ValueError) as e:
        return None, f"Video decode failed: {e}"


def _fps_time_base(rate):
    if not rate:
        return None
    return Fraction(rate.denominator, rate.numerator)


def _rescale_timestamp(value, source_time_base, target_time_base):
    if value is None or not source_time_base or not target_time_base or source_time_base == target_time_base:
        return value
    return int(round(value * Fraction(source_time_base) / Fraction(target_time_base)))


def _remux_audio_streams(source_path, out_container, audio_streams, out_audio_streams):
    if not audio_streams:
        return
    audio_container = av.open(source_path)
    try:
        remux_streams = list(audio_container.streams.audio)
        audio_map = {src.index: dst for src, dst in zip(remux_streams, out_audio_streams)}
        source_time_bases = {src.index: src.time_base for src in remux_streams}
        for packet in audio_container.demux(remux_streams):
            if packet.stream.index not in audio_map:
                continue
            out_stream = audio_map[packet.stream.index]
            source_time_base = packet.time_base or source_time_bases.get(packet.stream.index)
            target_time_base = out_stream.time_base or source_time_base
            packet.pts = _rescale_timestamp(packet.pts, source_time_base, target_time_base)
            packet.dts = _rescale_timestamp(packet.dts, source_time_base, target_time_base)
            packet.duration = _rescale_timestamp(packet.duration, source_time_base, target_time_base)
            packet.time_base = target_time_base
            packet.stream = out_stream
            if packet.pts is not None or packet.dts is not None:
                out_container.mux(packet)
    finally:
        audio_container.close()


def save_video_pyav(source_path: str, output_path: str, source_info: dict, modified_frames: dict, progress_cb=None):
    if not AV_AVAILABLE:
        raise RuntimeError("PyAV not installed. Run: pip install av")
    in_container = av.open(source_path)
    try:
        out_container = av.open(output_path, mode="w")
        try:
            src_stream = in_container.streams.video[0]
            audio_streams = list(in_container.streams.audio)
            source_rate = source_info.get("rate") or src_stream.average_rate or src_stream.base_rate or getattr(src_stream, "guessed_rate", None)
            if source_rate is None:
                raise RuntimeError("Could not determine source video frame rate.")
            out_stream = out_container.add_stream("libx264rgb", rate=source_rate)
            out_stream.width = source_info["width"]
            out_stream.height = source_info["height"]
            out_stream.pix_fmt = "rgb24"
            out_stream.options = {"crf": "0", "preset": "ultrafast"}
            source_time_base = source_info.get("time_base") or src_stream.time_base or _fps_time_base(source_rate)
            if source_time_base:
                out_stream.time_base = source_time_base
            out_audio_streams = [out_container.add_stream_from_template(stream) for stream in audio_streams]
            for src_audio, out_audio in zip(audio_streams, out_audio_streams):
                if src_audio.time_base:
                    out_audio.time_base = src_audio.time_base
            total = source_info["frames"]
            for frame_idx, frame in enumerate(in_container.decode(video=0)):
                if frame_idx in modified_frames:
                    new_frame = av.VideoFrame.from_ndarray(modified_frames[frame_idx], format="rgb24")
                else:
                    new_frame = av.VideoFrame.from_ndarray(frame.to_ndarray(format="rgb24"), format="rgb24")
                frame_time_base = frame.time_base or source_time_base
                target_time_base = out_stream.time_base or source_time_base
                if frame.pts is not None:
                    new_frame.pts = _rescale_timestamp(frame.pts, frame_time_base, target_time_base)
                    new_frame.time_base = target_time_base
                else:
                    frame_base = _fps_time_base(source_rate)
                    new_frame.pts = _rescale_timestamp(frame_idx, frame_base, target_time_base)
                    new_frame.time_base = target_time_base
                for packet in out_stream.encode(new_frame):
                    out_container.mux(packet)
                if progress_cb and total:
                    progress_cb(frame_idx / total)
            for packet in out_stream.encode():
                out_container.mux(packet)
            _remux_audio_streams(source_path, out_container, audio_streams, out_audio_streams)
        finally:
            out_container.close()
    finally:
        in_container.close()
    if progress_cb:
        progress_cb(1.0)


def encode_media(media_path: str, secret_data: bytes, technique: str, password_str: str, progress_cb=None):
    ext = os.path.splitext(media_path)[1].lower()
    if ext in (".png", ".bmp"):
        if technique == "LSB":
            return encode_lsb_image(media_path, secret_data, password_str)
        if technique == "PVD":
            return encode_pvd_image(media_path, secret_data, password_str)
    elif ext == ".wav" and technique == "LSB":
        return encode_audio(media_path, secret_data, password_str)
    elif ext in (".mkv", ".mov", ".avi", ".mp4") and technique == "LSB":
        return encode_video(media_path, secret_data, password_str, progress_cb)
    return None, f"'{technique}' is not supported for '{ext}' files."


def decode_media(media_path: str, technique: str, password_str: str, progress_cb=None):
    ext = os.path.splitext(media_path)[1].lower()
    if ext in (".png", ".bmp"):
        if technique == "LSB":
            return decode_lsb_image(media_path, password_str)
        if technique == "PVD":
            return decode_pvd_image(media_path, password_str)
    elif ext == ".wav" and technique == "LSB":
        return decode_audio(media_path, password_str)
    elif ext in (".mkv", ".mov", ".avi", ".mp4") and technique == "LSB":
        return decode_video(media_path, password_str, progress_cb)
    return None, f"Decoding '{technique}' for '{ext}' is not supported."


def save_stego_object(source_path: str, output_path: str, stego_obj, progress_cb=None) -> str:
    ext = os.path.splitext(source_path)[1].lower()
    if ext in (".png", ".bmp"):
        stego_obj.save(output_path)
    elif ext == ".wav":
        with wave.open(output_path, "wb") as wf:
            wf.setparams(stego_obj[1])
            wf.writeframes(stego_obj[0])
    elif ext in (".mkv", ".mov", ".avi", ".mp4"):
        if not output_path.lower().endswith(".mkv"):
            output_path += ".mkv"
        info, modified_frames = stego_obj
        save_video_pyav(source_path, output_path, info, modified_frames, progress_cb)
    else:
        raise ValueError(f"Unsupported output type for {ext}")
    return output_path
