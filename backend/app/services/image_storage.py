"""Private durable images on Vercel; ordinary installations retain local files."""
import logging
import os
import re
from pathlib import Path
from tempfile import NamedTemporaryFile

logger = logging.getLogger(__name__)


def enabled() -> bool:
    return bool(os.getenv("BLOB_READ_WRITE_TOKEN") or os.getenv("BLOB_STORE_ID"))


def _blob():
    from vercel.blob import sync
    return sync


def persist(path: Path) -> str:
    if not enabled():
        return str(path)
    uploaded = []
    try:
        for item in (path, path.with_suffix(".source")):
            if item.is_file():
                key = f"scans/{item.name}"
                _blob().put_blob(key, item.read_bytes(), access="private", content_type="image/jpeg" if item.suffix == ".jpg" else "application/octet-stream")
                uploaded.append(key)
    except Exception:
        if uploaded:
            try:
                _blob().delete_blob(uploaded)
            except Exception:
                logger.exception("Could not clean up an incomplete image upload")
        raise
    return f"blob://{path.name}"


def local_copy(stored_path: str, root: Path) -> Path:
    name = stored_path.removeprefix("blob://")
    if not re.fullmatch(r"[a-f0-9]{32}\.jpg", name):
        raise ValueError("Invalid stored image name")
    root.mkdir(parents=True, exist_ok=True)
    target = root / name
    if not target.exists():
        result = _blob().get_blob(f"scans/{name}", access="private")
        with NamedTemporaryFile(dir=root, delete=False) as temporary:
            temporary.write(result.body)
        os.replace(temporary.name, target)
    return target


def remove(stored_path: str) -> None:
    if stored_path.startswith("blob://"):
        name = stored_path.removeprefix("blob://")
        if not re.fullmatch(r"[a-f0-9]{32}\.jpg", name):
            raise ValueError("Invalid stored image name")
        _blob().delete_blob([f"scans/{name}", f"scans/{Path(name).with_suffix('.source')}"])
