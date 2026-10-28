"""Local CLIP food recognition, independent of freshness and package OCR."""
import json
import logging
import hashlib
import os
import tempfile
import urllib.request
from pathlib import Path
from threading import Lock

import numpy as np
import onnxruntime as ort
from PIL import Image, ImageOps

from app.core.config import settings

logger = logging.getLogger(__name__)
_model_lock = Lock()
_runtime = None
MODEL_NAME = "CLIP ViT-B/32 · int8 · local CPU"


def _cache_serverless_model(root: Path) -> None:
    """Fetch a fixed, verified public model once per Vercel instance."""
    model = root / "vision_model_int8.onnx"
    if model.is_file() or os.getenv("VERCEL") != "1":
        return
    url = "https://huggingface.co/Xenova/clip-vit-base-patch32/resolve/d15189d7028b43f1d3e65039190477f6af591c2a/onnx/vision_model_int8.onnx"
    digest = hashlib.sha256()
    with tempfile.NamedTemporaryFile(dir=root, delete=False) as output:
        temporary = Path(output.name)
        try:
            with urllib.request.urlopen(url, timeout=90) as response:
                while block := response.read(1024 * 1024):
                    digest.update(block)
                    output.write(block)
            output.close()
            if digest.hexdigest() != "0ab0c1b3ace708e539633af1744d5a95247fe4e14d3e08ff197ef82a6cb9bd93":
                raise RuntimeError("Product model checksum did not match the pinned release.")
            os.replace(temporary, model)
        finally:
            temporary.unlink(missing_ok=True)


def _load_runtime():
    global _runtime
    with _model_lock:
        if _runtime is None:
            root = Path(settings.MODEL_PATH)
            if not root.is_absolute():
                root = Path(__file__).resolve().parents[3] / root
            root = root / "product-recognition"
            _cache_serverless_model(root)
            options = ort.SessionOptions()
            options.intra_op_num_threads = 2
            options.inter_op_num_threads = 1
            session = ort.InferenceSession(str(root / "vision_model_int8.onnx"), sess_options=options, providers=["CPUExecutionProvider"])
            catalog = json.loads((root / "catalog.json").read_text())
            embeddings = np.load(root / "candidate_embeddings.npy", allow_pickle=False)
            processor = json.loads((root / "preprocessor_config.json").read_text())
            _runtime = session, catalog, embeddings, processor
        return _runtime


def recognize_image(image_path: str) -> dict:
    result = {
        "category": None, "product_name": None, "confidence": None,
        "confidence_kind": "cosine_similarity", "source": "unrecognized",
        "status": "unavailable", "model": MODEL_NAME, "evidence": [],
        "alternatives": [], "packaging": None,
        "limitations": ["Image recognition estimates the visible food type; it cannot establish ingredients, allergens, expiry, or safety."],
    }
    if not settings.PRODUCT_RECOGNITION_ENABLED:
        result["limitations"].append("Image recognition is disabled in this environment.")
        return result
    try:
        session, catalog, embeddings, processor = _load_runtime()
    except (OSError, ort.capi.onnxruntime_pybind11_state.Fail, ort.capi.onnxruntime_pybind11_state.NoSuchFile):
        logger.exception("Product recognition model is unavailable; run scripts/setup_product_recognition.py")
        result["limitations"].append("Image recognition is temporarily unavailable. Readable package text can still identify the product.")
        return result
    crop = processor["crop_size"]
    size = (crop["width"], crop["height"]) if isinstance(crop, dict) else (crop, crop)
    with Image.open(image_path) as original:
        image = ImageOps.fit(original.convert("RGB"), size, method=Image.Resampling.BICUBIC)
        pixels = np.asarray(image, dtype=np.float32) / 255.0
    pixels = (pixels - np.asarray(processor["image_mean"], dtype=np.float32)) / np.asarray(processor["image_std"], dtype=np.float32)
    vector = session.run(["image_embeds"], {"pixel_values": pixels.transpose(2, 0, 1)[None]})[0][0]
    vector /= np.linalg.norm(vector)
    scores = embeddings @ vector
    candidates = catalog["candidates"]
    ranked = np.argsort(scores[:len(candidates)])[::-1]
    best = candidates[int(ranked[0])]
    score = float(scores[ranked[0]])
    result.update(source="image_model", status="uncertain", confidence=round(score, 4))
    result["alternatives"] = [
        {"name": candidates[int(index)]["name"], "category": candidates[int(index)]["category"], "similarity": round(float(scores[index]), 4)}
        for index in ranked[:3]
    ]
    if best["category"] is None:
        result.update(status="not_food", product_name="No food visible")
        result["evidence"] = ["The strongest visual match is a nonfood scene."]
        return result
    if score < 0.23:
        result["product_name"] = "Food identification needs a clearer photo"
        result["evidence"] = ["The image has only weak matches to the supported food categories."]
        return result
    result.update(category=best["category"], product_name=best["name"])
    margin = score - float(scores[ranked[1]])
    if score >= 0.26 and margin >= 0.015 and best["category"] != "Packaged food":
        result["status"] = "recognized"
    else:
        if best["category"] != "Packaged food":
            result["product_name"] = f"{best['category']} · exact food type uncertain"
        result["limitations"].append("This is a tentative visual match; compare the alternatives and confirm the product.")
    result["evidence"] = [f"Visual match: {best['name']}", f"Image/text similarity: {score:.3f}; not a probability"]
    packaging_scores = scores[len(candidates):]
    packaging_index = int(packaging_scores.argmax())
    if packaging_scores[packaging_index] >= 0.23:
        result["packaging"] = catalog["packaging"][packaging_index]
    if best["category"] == "Packaged food":
        result["limitations"].append("Only the package or lid is visible. Photograph the front label to identify its contents.")
    return result
