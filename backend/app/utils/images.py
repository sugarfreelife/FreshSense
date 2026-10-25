"""Safe image decoding and normalization for scan uploads."""

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

try:
    import pillow_heif

    pillow_heif.register_heif_opener()
except ImportError:
    pass

MAX_IMAGE_PIXELS = 40_000_000
MAX_IMAGE_EDGE = 2_560
SUPPORTED_UPLOAD_FORMATS = {
    "JPEG", "PNG", "WEBP", "GIF", "BMP", "DIB", "TIFF", "AVIF", "HEIF",
    "JPEG2000", "ICO", "TGA", "PCX", "PPM", "PGM", "PBM", "QOI", "SGI",
}


def normalize_uploaded_image(contents: bytes, destination: str | Path) -> str:
    """Decode a common raster format and store a browser-friendly, oriented JPEG.

    Normalizing once avoids downstream OCR/model format surprises and caps huge
    camera images before the comparatively expensive OCR stage.
    """
    try:
        with Image.open(BytesIO(contents)) as source:
            if (source.format or "").upper() not in SUPPORTED_UPLOAD_FORMATS:
                raise ValueError("Unsupported image format. Use a common photo format such as JPEG, PNG, WebP, GIF, TIFF, BMP, AVIF, or HEIC.")
            if source.width <= 0 or source.height <= 0 or source.width * source.height > MAX_IMAGE_PIXELS:
                raise ValueError("Image dimensions are too large. Choose a photo smaller than 40 megapixels.")

            if getattr(source, "is_animated", False):
                source.seek(0)
            oriented = ImageOps.exif_transpose(source)
            oriented.thumbnail((MAX_IMAGE_EDGE, MAX_IMAGE_EDGE), Image.Resampling.LANCZOS)
            if "A" in oriented.getbands():
                rgba = oriented.convert("RGBA")
                background = Image.new("RGB", rgba.size, "white")
                background.paste(rgba, mask=rgba.getchannel("A"))
                rgb = background
                rgba.close()
            else:
                rgb = oriented.convert("RGB")
            rgb.save(destination, format="JPEG", quality=90, optimize=False)
            rgb.close()
            if oriented is not source:
                oriented.close()
        return "JPEG"
    except ValueError:
        raise
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError("Could not decode this image. Try a standard JPEG, PNG, WebP, or HEIC photo.") from exc


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
