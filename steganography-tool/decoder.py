from __future__ import annotations

import random

import numpy as np
from PIL import Image

from encryption import decrypt_data, derive_shuffle_seed
from utils import (
    InvalidImageError,
    PUBLIC_HEADER_MAGIC,
    PUBLIC_HEADER_SIZE,
    PUBLIC_HEADER_STRUCT,
    emit_progress,
    parse_bundle,
)


def _bits_to_bytes(bits: np.ndarray) -> bytes:
    return np.packbits(bits).tobytes()


def _candidate_channels(array: np.ndarray) -> np.ndarray:
    # Ignore the least-significant bit so we reproduce the same ranking used at encode time.
    rgb = array[:, :, :3] & 0xFE
    gray = (
        0.299 * rgb[:, :, 0].astype(np.float32)
        + 0.587 * rgb[:, :, 1].astype(np.float32)
        + 0.114 * rgb[:, :, 2].astype(np.float32)
    )
    dx = np.zeros_like(gray)
    dy = np.zeros_like(gray)
    dx[:, :-1] = np.abs(gray[:, 1:] - gray[:, :-1])
    dy[:-1, :] = np.abs(gray[1:, :] - gray[:-1, :])
    scores = (dx + dy).reshape(-1)
    pixel_order = np.argsort(scores)[::-1]
    ranked = np.concatenate([pixel_order * 3 + i for i in range(3)]).astype(np.int64, copy=False)
    if array.shape[2] == 4:
        alpha = array[:, :, 3].reshape(-1)
        alpha_mask = np.repeat(alpha > 0, 3)
        ranked = ranked[alpha_mask[ranked]]
    _, index = np.unique(ranked, return_index=True)
    return ranked[np.sort(index)]


def decode_payload(image_path: str, password: str, progress_callback=None):
    emit_progress(progress_callback, 0.05, "Loading image")
    with Image.open(image_path) as image:
        carrier = image.convert("RGBA")

    array = np.array(carrier, dtype=np.uint8)
    flat_rgb = array[:, :, :3].reshape(-1)

    emit_progress(progress_callback, 0.2, "Reading hidden header")
    header_bits = flat_rgb[: PUBLIC_HEADER_SIZE * 8] & 1
    header_data = _bits_to_bytes(header_bits)
    magic, version, salt, shuffle_salt, nonce, ciphertext_len = PUBLIC_HEADER_STRUCT.unpack(header_data)

    if magic != PUBLIC_HEADER_MAGIC or version != 1:
        raise InvalidImageError("No valid Secure Steganography payload was found in this image.")

    payload_bits_len = ciphertext_len * 8
    reserved = PUBLIC_HEADER_SIZE * 8
    candidates = _candidate_channels(array)
    candidates = candidates[candidates >= reserved]
    if len(candidates) < payload_bits_len:
        candidates = np.arange(reserved, flat_rgb.size, dtype=np.int64)

    emit_progress(progress_callback, 0.45, "Locating randomized payload")
    rng = random.Random(derive_shuffle_seed(password, shuffle_salt))
    candidate_list = candidates.tolist()
    rng.shuffle(candidate_list)
    positions = np.array(candidate_list[:payload_bits_len], dtype=np.int64)
    payload_bits = flat_rgb[positions] & 1
    ciphertext = _bits_to_bytes(payload_bits)

    emit_progress(progress_callback, 0.7, "Authenticating and decrypting")
    bundle = decrypt_data(ciphertext, password, salt, nonce)
    package = parse_bundle(bundle)
    emit_progress(progress_callback, 1.0, "Decoding complete")
    return package
