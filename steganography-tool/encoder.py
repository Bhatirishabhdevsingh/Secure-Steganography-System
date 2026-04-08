from __future__ import annotations

import math
import random
from pathlib import Path

import numpy as np
from PIL import Image

from encryption import derive_shuffle_seed, encrypt_data
from utils import (
    CapacityError,
    PUBLIC_HEADER_MAGIC,
    PUBLIC_HEADER_SIZE,
    PUBLIC_HEADER_STRUCT,
    build_bundle,
    emit_progress,
)


def _to_bits(data: bytes) -> np.ndarray:
    return np.unpackbits(np.frombuffer(data, dtype=np.uint8))


def _from_bits(bits: np.ndarray) -> bytes:
    return np.packbits(bits).tobytes()


def _texture_rank(rgb: np.ndarray) -> np.ndarray:
    # Ignore the least-significant bit so the ranking stays stable after embedding.
    rgb = rgb & 0xFE
    gray = (
        0.299 * rgb[:, :, 0].astype(np.float32)
        + 0.587 * rgb[:, :, 1].astype(np.float32)
        + 0.114 * rgb[:, :, 2].astype(np.float32)
    )
    dx = np.zeros_like(gray)
    dy = np.zeros_like(gray)
    dx[:, :-1] = np.abs(gray[:, 1:] - gray[:, :-1])
    dy[:-1, :] = np.abs(gray[1:, :] - gray[:-1, :])
    return (dx + dy).reshape(-1)


def _candidate_channels(array: np.ndarray) -> np.ndarray:
    rgb = array[:, :, :3]
    flat_channels = np.arange(rgb.size, dtype=np.int64)
    scores = _texture_rank(rgb)
    pixel_order = np.argsort(scores)[::-1]
    ranked = np.concatenate([pixel_order * 3 + i for i in range(3)])
    ranked = ranked.astype(np.int64, copy=False)

    alpha_mask = None
    if array.shape[2] == 4:
        alpha = array[:, :, 3].reshape(-1)
        alpha_mask = np.repeat(alpha > 0, 3)

    if alpha_mask is not None:
        ranked = ranked[alpha_mask[ranked]]

    # Deduplicate after concatenation while preserving order.
    _, index = np.unique(ranked, return_index=True)
    return ranked[np.sort(index)] if len(index) else flat_channels


def _embed_bits(array: np.ndarray, positions: np.ndarray, bits: np.ndarray) -> np.ndarray:
    flat = array[:, :, :3].reshape(-1).copy()
    selected = flat[positions]
    selected = (selected & 0xFE) | bits
    flat[positions] = selected
    result = array.copy()
    result[:, :, :3] = flat.reshape(array[:, :, :3].shape)
    return result


def encode_payload(
    image_path: str,
    package,
    password: str,
    output_path: str,
    progress_callback=None,
) -> dict:
    emit_progress(progress_callback, 0.05, "Loading image")
    with Image.open(image_path) as image:
        carrier = image.convert("RGBA")

    array = np.array(carrier, dtype=np.uint8)
    emit_progress(progress_callback, 0.15, "Preparing encrypted payload")
    bundle = build_bundle(package)
    salt, shuffle_salt, ciphertext = None, None, None
    salt, nonce, ciphertext = encrypt_data(bundle, password)
    shuffle_salt = salt[::-1]

    public_header = PUBLIC_HEADER_STRUCT.pack(
        PUBLIC_HEADER_MAGIC,
        1,
        salt,
        shuffle_salt,
        nonce,
        len(ciphertext),
    )
    header_bits = _to_bits(public_header)
    payload_bits = _to_bits(ciphertext)

    rgb_capacity_bits = array[:, :, :3].size
    reserved = len(header_bits)
    available_payload_bits = rgb_capacity_bits - reserved
    if available_payload_bits < len(payload_bits):
        raise CapacityError(
            f"Image capacity exceeded. Need {math.ceil((len(payload_bits) - available_payload_bits) / 8)} more bytes."
        )

    emit_progress(progress_callback, 0.3, "Selecting stealth embedding positions")
    sequential_positions = np.arange(reserved, dtype=np.int64)
    candidates = _candidate_channels(array)
    candidates = candidates[candidates >= reserved]
    if len(candidates) < len(payload_bits):
        candidates = np.arange(reserved, rgb_capacity_bits, dtype=np.int64)

    rng = random.Random(derive_shuffle_seed(password, shuffle_salt))
    candidate_list = candidates.tolist()
    rng.shuffle(candidate_list)
    payload_positions = np.array(candidate_list[: len(payload_bits)], dtype=np.int64)

    emit_progress(progress_callback, 0.55, "Embedding hidden content")
    flat_rgb = array[:, :, :3].reshape(-1).copy()
    flat_rgb[sequential_positions] = (flat_rgb[sequential_positions] & 0xFE) | header_bits
    flat_rgb[payload_positions] = (flat_rgb[payload_positions] & 0xFE) | payload_bits
    array[:, :, :3] = flat_rgb.reshape(array[:, :, :3].shape)

    emit_progress(progress_callback, 0.8, "Saving stego image")
    output = Image.fromarray(array, mode="RGBA")
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    output.save(destination, format="PNG", optimize=False)

    emit_progress(progress_callback, 1.0, "Encoding complete")
    return {
        "output_path": str(destination),
        "ciphertext_bytes": len(ciphertext),
        "carrier_capacity_bytes": available_payload_bits // 8,
        "bundle_bytes": len(bundle),
    }
