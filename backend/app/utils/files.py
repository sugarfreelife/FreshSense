"""File upload validation helpers."""

import os

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


def validate_extension(filename: str) -> bool:
    return os.path.splitext(filename.lower())[1] in ALLOWED_EXTENSIONS


def validate_mime(content_type: str | None) -> bool:
    mime_type = (content_type or "").split(";", 1)[0].strip().lower()
    return mime_type in ALLOWED_MIME_TYPES


def validate_size(size_bytes: int) -> bool:
    return 0 < size_bytes <= MAX_FILE_SIZE_BYTES
