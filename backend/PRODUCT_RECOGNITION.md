# Food and product recognition

FreshSense uses the pretrained CLIP ViT-B/32 image encoder, quantized to int8
ONNX, to compare a photograph with 109 candidate food and nonfood descriptions.
It runs locally on the CPU. There is no cloud key and scan images stay local.
Results include a likely food name/category, similarity, three candidate matches,
likely packaging, and uncertainty. The separate freshness model remains a color
and brightness prototype unless a reviewed freshness artifact is installed.

## Install and prepare

From `backend`, using the project's Python environment:

```sh
.venv/bin/pip install -r requirements-model-setup.txt
.venv/bin/python scripts/setup_product_recognition.py
.venv/bin/python -m alembic upgrade head
```

Setup downloads approximately 153 MB from
[Xenova/clip-vit-base-patch32](https://huggingface.co/Xenova/clip-vit-base-patch32),
pinned to revision `d15189d7028b43f1d3e65039190477f6af591c2a`. It verifies the
SHA256 hashes of both models and precomputes the candidate text embeddings.
Weights and embeddings live in `backend/models/product-recognition/`, ignored
by Git. Docker's existing models mount exposes these files to the API. Only
NumPy and ONNX Runtime are needed during scans; the tokenizer is needed for
setup. Restart the API after replacing model assets.

`PRODUCT_RECOGNITION_ENABLED=false` disables image identity inference, for
example in isolated tests. Missing model assets are disclosed in the result;
the API does not download models during uploads. Use **Analyze photo again**
to apply recognition to old scans. Results are saved with each scan, retained
on reload and in history. Existing scans are not silently rewritten.

## What the result means

CLIP ranks a bounded food catalog. Cosine similarity is not a probability or
measured accuracy. The acceptance thresholds (similarity 0.26 and separation
0.015) are heuristics, not calibrated accuracy guarantees. Weaker matches are
tentative; unsupported or nonfood images may require another photo. Recognition
describes the dominant image, without bounding boxes or counting every item.
Photograph one food/product at a time.

OCR independently extracts visible package text and dates. Package-text category
matches take priority. Agreeing image and text evidence is labelled explicitly;
disagreements remain visible. Ingredients, allergen statements, nutrition,
storage instructions and package size are readable text excerpts only. The
model cannot infer invisible label details, exact brands, manufacturing origins,
expiry dates, or food safety. A can-lid photo can identify packaging but cannot
establish hidden contents. Dates need confirmation against the physical package.
No broad recognition accuracy is claimed from a few sample checks.

To change the vocabulary, edit `app/ml/vision/product_catalog.py` and rerun setup
to regenerate embeddings. The source model is based on
[OpenAI CLIP](https://github.com/openai/CLIP), distributed under the MIT license;
consult its model card for intended uses and limitations.
