"""Check evidence provenance, label extraction, and saved recognition results."""
from io import BytesIO

import numpy as np
from PIL import Image

from app.api.v1.endpoints import scans
from app.ml.vision import product_recognition
from app.services.product_service import identify_product


def test_visual_recognition_survives_weak_ocr_without_invented_details():
    product = identify_product({
        "source": "image_model", "status": "recognized", "category": "Beverages",
        "product_name": "Cola soft drink", "evidence": ["Visible drink can"],
    }, "ORIJINAL TAT")
    assert product["product_name"] == "Cola soft drink"
    assert product["source"] == "image_model"
    assert all(value is None for value in product["label_details"].values())


def test_readable_ingredients_and_allergens_are_preserved_as_label_evidence():
    product = identify_product(None, "Milk 500 ml\nIngredients: milk, cocoa\nContains: milk\nStorage: keep refrigerated")
    assert product["source"] == "package_text"
    assert product["label_details"] == {
        "package_size": "500 ml", "ingredients": "milk, cocoa", "allergens": "milk",
        "storage_instructions": "keep refrigerated", "nutrition_text": None,
    }


def test_disagreeing_label_and_visual_categories_keep_conflict_visible():
    product = identify_product({
        "category": "Beverages", "source": "image_model", "product_name": "Cola soft drink",
        "alternatives": [{"name": "Cola soft drink", "category": "Beverages", "similarity": 0.3}],
    }, "Whole wheat bread")
    assert product["category"] == "Bread & bakery"
    assert product["source"] == "package_text"
    assert "compare" in product["limitations"][0]
    assert product["alternatives"][0]["category"] == "Beverages"


def test_close_visual_matches_preserve_category_without_claiming_an_exact_food(tmp_path, monkeypatch):
    class ImageEncoder:
        def run(self, names, inputs):
            return [np.array([[1.0, 0.0]], dtype=np.float32)]

    path = tmp_path / "grapes.jpg"
    Image.new("RGB", (32, 32), "green").save(path)
    catalog = {
        "candidates": [
            {"name": "Lime", "category": "Produce"},
            {"name": "Grapes", "category": "Produce"},
        ],
        "packaging": ["unpackaged fruit or vegetables"],
    }
    scores = np.array([0.2859, 0.2855, 0.24], dtype=np.float32)
    embeddings = np.column_stack([scores, np.sqrt(1 - scores ** 2)])
    processor = {"crop_size": 32, "image_mean": [0, 0, 0], "image_std": [1, 1, 1]}
    monkeypatch.setattr(product_recognition.settings, "PRODUCT_RECOGNITION_ENABLED", True)
    monkeypatch.setattr(product_recognition, "_load_runtime", lambda: (ImageEncoder(), catalog, embeddings, processor))

    result = product_recognition.recognize_image(str(path))

    assert result["status"] == "uncertain"
    assert result["category"] == "Produce"
    assert result["product_name"] == "Produce · exact food type uncertain"
    assert [item["name"] for item in result["alternatives"]] == ["Lime", "Grapes"]


def test_scan_saves_image_recognition_and_reads_it_back(client, auth_headers, monkeypatch):
    monkeypatch.setattr(scans, "predict_image", lambda path: {
        "food_type": "Beverages", "freshness": "fresh", "confidence": 0.6,
        "model_type": "prototype", "model_version": "test",
        "product_recognition": {
            "source": "image_model", "status": "recognized", "category": "Beverages",
            "product_name": "Cola soft drink", "packaging": "aluminum drink can",
            "confidence": 0.3, "confidence_kind": "cosine_similarity",
        },
    })
    monkeypatch.setattr(scans, "extract_text_from_image", lambda path: {"raw_text": "ORIJINAL TAT"})
    buffer = BytesIO()
    Image.new("RGB", (64, 128), "red").save(buffer, format="JPEG")
    response = client.post("/api/v1/scans", headers=auth_headers, files={"file": ("can.jpg", buffer.getvalue(), "image/jpeg")})
    assert response.status_code == 201, response.text
    saved = response.json()
    assert saved["food_label"] is None
    assert saved["product"]["product_name"] == "Cola soft drink"
    reread = client.get(f"/api/v1/scans/{saved['id']}", headers=auth_headers)
    assert reread.status_code == 200
    assert reread.json()["product"] == saved["product"]
    assert any("image" in event["detail"] for event in saved["passport"]["timeline"] if event["key"] == "product")
