"""Vision preprocessing helpers (PIL-based, no trained weights)."""

from PIL import Image


def load_and_resize(image_path: str, size: tuple[int, int] = (224, 224)) -> Image.Image:
    with Image.open(image_path) as source:
        return source.convert("RGB").resize(size, Image.Resampling.LANCZOS)


def average_color(img: Image.Image) -> tuple[float, float, float]:
    pixels = img.get_flattened_data()
    n = max(len(pixels), 1)
    r = sum(p[0] for p in pixels) / n
    g = sum(p[1] for p in pixels) / n
    b = sum(p[2] for p in pixels) / n
    return (r, g, b)


def dark_ratio(img: Image.Image, threshold: int = 60) -> float:
    pixels = img.get_flattened_data()
    n = max(len(pixels), 1)
    dark = sum(1 for p in pixels if sum(p) / 3 < threshold)
    return dark / n
