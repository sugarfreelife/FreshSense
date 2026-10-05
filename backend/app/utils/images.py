"""Image helpers."""

from PIL import Image

MAX_IMAGE_PIXELS = 40_000_000


def verify_image(path: str) -> bool:
    try:
        with Image.open(path) as img:
            if img.width <= 0 or img.height <= 0 or img.width * img.height > MAX_IMAGE_PIXELS:
                return False
            img.verify()
        return True
    except Exception:
        return False


def open_rgb(path: str) -> Image.Image:
    with Image.open(path) as image:
        return image.convert("RGB")
