"""Vercel ASGI entrypoint. Durable scan images use the connected private store."""
import os
import sys
import shutil
from pathlib import Path

backend = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend))
os.environ.setdefault("UPLOAD_DIR", "/tmp/freshsense-uploads")
os.environ.setdefault("MODEL_PATH", "/tmp/freshsense-models")
if not (os.getenv("BLOB_READ_WRITE_TOKEN") or os.getenv("BLOB_STORE_ID")):
    raise RuntimeError("Connect the private scan-photo Blob store before deploying the API.")

# Small model metadata ships with the API; weights are cached on the first scan.
model_dir = Path(os.environ["MODEL_PATH"]) / "product-recognition"
model_dir.mkdir(parents=True, exist_ok=True)
for name in ("catalog.json", "candidate_embeddings.npy", "preprocessor_config.json"):
    shutil.copyfile(backend / "models" / "product-recognition" / name, model_dir / name)

from app.main import app  # noqa: E402,F401
