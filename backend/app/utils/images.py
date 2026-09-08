"""Image helpers."""

from PIL import Image


def verify_image(path: str) -> bool:
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except Exception:
        return False


def open_rgb(path: str) -> Image.Image:
    return Image.open(path).convert("RGB")
