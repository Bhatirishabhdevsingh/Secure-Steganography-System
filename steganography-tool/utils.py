from __future__ import annotations

import json
import logging
import mimetypes
import os
import struct
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from PIL import Image

APP_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = APP_ROOT / "output"
LOG_DIR = APP_ROOT / "logs"
PUBLIC_HEADER_MAGIC = b"SSG1"
PUBLIC_HEADER_STRUCT = struct.Struct(">4sB16s16s12sQ")
PUBLIC_HEADER_SIZE = PUBLIC_HEADER_STRUCT.size
BUNDLE_HEADER_MAGIC = b"BDL1"
BUNDLE_HEADER_STRUCT = struct.Struct(">4sBHHQ")


class SteganographyError(Exception):
    """Base exception for secure steganography operations."""


class CapacityError(SteganographyError):
    """Raised when the selected image cannot hold the payload."""


class InvalidImageError(SteganographyError):
    """Raised when the image or its hidden payload is invalid."""


class AuthenticationError(SteganographyError):
    """Raised when decryption fails due to an invalid password or tampered data."""


@dataclass
class PayloadPackage:
    payload_type: str
    data: bytes
    file_name: str = ""
    mime_type: str = "application/octet-stream"


def ensure_directories() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def setup_logging() -> logging.Logger:
    ensure_directories()
    logger = logging.getLogger("secure_steganography")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(LOG_DIR / "operations.log", encoding="utf-8")
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def log_operation(action: str, source: str, status: str, size: int, details: str = "") -> None:
    logger = setup_logging()
    logger.info(
        "%s | source=%s | bytes=%s | status=%s | %s",
        action,
        source,
        size,
        status,
        details,
    )


def read_text_payload(text: str) -> PayloadPackage:
    return PayloadPackage(
        payload_type="text",
        data=text.encode("utf-8"),
        file_name="message.txt",
        mime_type="text/plain",
    )


def read_file_payload(file_path: str) -> PayloadPackage:
    path = Path(file_path)
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return PayloadPackage(
        payload_type="file",
        data=path.read_bytes(),
        file_name=path.name,
        mime_type=mime_type,
    )


def build_bundle(package: PayloadPackage) -> bytes:
    file_name = package.file_name.encode("utf-8")
    mime_type = package.mime_type.encode("utf-8")
    payload_type = 0 if package.payload_type == "text" else 1
    header = BUNDLE_HEADER_STRUCT.pack(
        BUNDLE_HEADER_MAGIC,
        payload_type,
        len(file_name),
        len(mime_type),
        len(package.data),
    )
    return header + file_name + mime_type + package.data


def parse_bundle(bundle: bytes) -> PayloadPackage:
    if len(bundle) < BUNDLE_HEADER_STRUCT.size:
        raise InvalidImageError("Hidden data is incomplete or corrupted.")

    magic, payload_type, name_len, mime_len, data_len = BUNDLE_HEADER_STRUCT.unpack(
        bundle[: BUNDLE_HEADER_STRUCT.size]
    )
    if magic != BUNDLE_HEADER_MAGIC:
        raise InvalidImageError("Hidden data header is invalid.")

    offset = BUNDLE_HEADER_STRUCT.size
    name_bytes = bundle[offset : offset + name_len]
    offset += name_len
    mime_bytes = bundle[offset : offset + mime_len]
    offset += mime_len
    data = bundle[offset : offset + data_len]
    if len(data) != data_len:
        raise InvalidImageError("Hidden data payload is truncated.")

    return PayloadPackage(
        payload_type="text" if payload_type == 0 else "file",
        data=data,
        file_name=name_bytes.decode("utf-8", errors="ignore"),
        mime_type=mime_bytes.decode("utf-8", errors="ignore") or "application/octet-stream",
    )


def format_bytes(size: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{size} B"


def timestamped_output_path(base_name: str, suffix: str) -> str:
    ensure_directories()
    stem = Path(base_name).stem or "stego"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return str(OUTPUT_DIR / f"{stem}_{stamp}{suffix}")


def save_extracted_package(package: PayloadPackage, destination_dir: Optional[str] = None) -> str:
    ensure_directories()
    target_dir = Path(destination_dir) if destination_dir else OUTPUT_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    if package.payload_type == "text":
        path = target_dir / f"extracted_message_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        path.write_text(package.data.decode("utf-8", errors="replace"), encoding="utf-8")
        return str(path)

    safe_name = package.file_name or f"extracted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bin"
    path = target_dir / safe_name
    if path.exists():
        path = target_dir / f"{path.stem}_{datetime.now().strftime('%H%M%S')}{path.suffix}"
    path.write_bytes(package.data)
    return str(path)


def image_summary(path: str) -> dict:
    with Image.open(path) as image:
        return {
            "format": image.format,
            "mode": image.mode,
            "size": image.size,
        }


ProgressCallback = Optional[Callable[[float, str], None]]


def emit_progress(callback: ProgressCallback, percent: float, message: str) -> None:
    if callback:
        callback(percent, message)


def serialize_preview(package: PayloadPackage) -> str:
    preview = {
        "type": package.payload_type,
        "name": package.file_name,
        "mime": package.mime_type,
        "size": len(package.data),
    }
    if package.payload_type == "text":
        preview["snippet"] = package.data.decode("utf-8", errors="replace")[:200]
    return json.dumps(preview, indent=2)
