"""Download pinned, public CLIP ONNX weights and prepare candidate embeddings.

Run from backend: .venv/bin/python scripts/setup_product_recognition.py
Install requirements-model-setup.txt before running this script.
The application never downloads weights during a user's scan.
"""
import hashlib
import json
from pathlib import Path
import sys
import urllib.request

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from app.ml.vision.product_catalog import CANDIDATES, PACKAGING
from app.core.config import settings

REVISION = "d15189d7028b43f1d3e65039190477f6af591c2a"
BASE_URL = f"https://huggingface.co/Xenova/clip-vit-base-patch32/resolve/{REVISION}"
FILES = {
    "vision_model_int8.onnx": ("onnx/vision_model_int8.onnx", "0ab0c1b3ace708e539633af1744d5a95247fe4e14d3e08ff197ef82a6cb9bd93"),
    "text_model_int8.onnx": ("onnx/text_model_int8.onnx", "18845f2ccc35223bb7fec403383a131154b11ac0918df25cf51986df5efd3a21"),
    "tokenizer.json": ("tokenizer.json", None),
    "preprocessor_config.json": ("preprocessor_config.json", None),
}


def main():
    model_root = Path(settings.MODEL_PATH)
    if not model_root.is_absolute():
        model_root = BACKEND / model_root
    model_root = model_root.resolve() / "product-recognition"
    model_root.mkdir(parents=True, exist_ok=True)
    for local_name, (remote, checksum) in FILES.items():
        dest = model_root / local_name
        if not dest.is_file():
            print(f"Downloading {remote}…", flush=True)
            temporary = dest.with_suffix(dest.suffix + ".tmp")
            with urllib.request.urlopen(f"{BASE_URL}/{remote}", timeout=120) as response, temporary.open("wb") as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
            temporary.replace(dest)
        if checksum and hashlib.sha256(dest.read_bytes()).hexdigest() != checksum:
            raise RuntimeError(f"Checksum mismatch for {dest}; remove it and rerun setup.")
    tokenizer = Tokenizer.from_file(str(model_root / "tokenizer.json"))
    tokenizer.enable_truncation(max_length=77)
    tokenizer.enable_padding(length=77, pad_id=49407, pad_token="<|endoftext|>")
    prompts = [item["prompt"] for item in CANDIDATES] + [f"a photo of {item}" for item in PACKAGING]
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    session = ort.InferenceSession(str(model_root / "text_model_int8.onnx"), sess_options=options, providers=["CPUExecutionProvider"])
    embeddings = []
    for start in range(0, len(prompts), 8):
        tokens = tokenizer.encode_batch(prompts[start:start + 8])
        feeds = {"input_ids": np.array([item.ids for item in tokens], dtype=np.int64)}
        if "attention_mask" in {item.name for item in session.get_inputs()}:
            feeds["attention_mask"] = np.array([item.attention_mask for item in tokens], dtype=np.int64)
        output = session.run(["text_embeds"], feeds)[0]
        embeddings.extend(output / np.linalg.norm(output, axis=-1, keepdims=True))
    np.save(model_root / "candidate_embeddings.npy", np.asarray(embeddings, dtype=np.float32))
    (model_root / "catalog.json").write_text(json.dumps({"revision": REVISION, "candidates": CANDIDATES, "packaging": PACKAGING}, indent=2))
    print(f"Ready: {len(CANDIDATES)} food/nonfood candidates and {len(PACKAGING)} packaging descriptions in {model_root}")


if __name__ == "__main__":
    main()
