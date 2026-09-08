"""PROTOTYPE HEURISTIC — NOT a trained model.

Analyzes average color / dark-pixel ratio with PIL to produce a rough
freshness guess for demo purposes only. Must not be presented as AI accuracy.
"""

import os

from app.ml.vision.preprocessing import average_color, dark_ratio, load_and_resize

MODEL_VERSION = "vision-v0.1-prototype"

_KNOWN_FOODS = ("apple", "banana", "bread", "milk", "tomato", "lettuce", "egg", "cheese", "meat", "fish")


def guess_food_type(filename: str) -> str:
    stem = os.path.basename(filename).lower()
    for food in _KNOWN_FOODS:
        if food in stem:
            return food
    return "unknown"


def heuristic_predict(image_path: str) -> dict:
    img = load_and_resize(image_path)
    r, g, b = average_color(img)
    dark = dark_ratio(img)
    brightness = (r + g + b) / 3.0

    # Simple documented heuristic: very dark / brownish images -> spoiled.
    if dark > 0.55 or (brightness < 55 and r < 90):
        freshness, confidence = "spoiled", 0.65
    elif dark > 0.35 or brightness < 90:
        freshness, confidence = "moderately_fresh", 0.55
    else:
        freshness, confidence = "fresh", 0.6

    return {
        "food_type": guess_food_type(image_path),
        "freshness": freshness,
        "confidence": round(float(confidence), 3),
        "model_version": MODEL_VERSION,
        "model_type": "prototype",
        "note": "Prototype heuristic only; not a trained model.",
    }
