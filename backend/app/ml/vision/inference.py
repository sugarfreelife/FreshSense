"""Vision prediction with a transparent heuristic fallback and trained model path."""

import json
from math import exp, isfinite
from pathlib import Path

from app.core.enums import FreshnessEnum
from app.ml.vision.features import FEATURE_NAMES, LEGACY_FEATURE_NAMES, extract_image_features

MODEL_VERSION = "vision-v0.2-prototype"
TRAINED_MODEL_FILENAME = "vision_model.json"


def heuristic_predict(image_path: str) -> dict:
    _, evidence = extract_image_features(image_path)
    dark = evidence["dark_pixel_ratio"]
    brightness = evidence["mean_brightness"]

    # Preserve conservative demo behavior until labeled local images can train a model.
    if dark > 0.55 or brightness < 45:
        freshness, confidence = "spoiled", 0.65
    elif dark > 0.35 or brightness < 90:
        freshness, confidence = "moderately_fresh", 0.55
    else:
        freshness, confidence = "fresh", 0.6

    return {
        "food_type": "unknown",
        "freshness": freshness,
        "confidence": round(float(confidence), 3),
        "confidence_kind": "heuristic_score",
        "model_version": MODEL_VERSION,
        "model_type": "prototype",
        "visual_evidence": evidence,
        "note": "Prototype heuristic only; not a trained model.",
    }


def _softmax(logits: list[float]) -> list[float]:
    peak = max(logits)
    exponentials = [exp(value - peak) for value in logits]
    total = sum(exponentials)
    return [value / total for value in exponentials]


def _predict_with_artifact(image_path: str, artifact_path: Path) -> dict:
    with artifact_path.open(encoding="utf-8") as model_file:
        artifact = json.load(model_file)
    if not isinstance(artifact, dict):
        raise ValueError("Trained vision model artifact must be a JSON object.")
    if artifact.get("schema_version") != 1:
        raise ValueError("Trained vision model artifact version is not supported.")
    artifact_features = artifact.get("feature_names")
    if artifact_features not in (list(FEATURE_NAMES), list(LEGACY_FEATURE_NAMES)):
        raise ValueError("Trained vision model feature schema does not match this application.")
    classes = [value.value for value in FreshnessEnum]
    if artifact.get("classes") != classes:
        raise ValueError("Trained vision model classes do not match the supported freshness labels.")

    means = artifact.get("means")
    scales = artifact.get("scales")
    weights = artifact.get("weights")
    biases = artifact.get("bias")
    feature_count = len(artifact_features)
    if (
        not isinstance(means, list)
        or not isinstance(scales, list)
        or len(means) != feature_count
        or len(scales) != feature_count
        or not isinstance(weights, list)
        or len(weights) != len(classes)
        or not isinstance(biases, list)
        or len(biases) != len(classes)
        or any(not isinstance(row, list) or len(row) != feature_count for row in weights)
    ):
        raise ValueError("Trained vision model artifact has invalid parameter dimensions.")
    parameters = means + scales + biases + [weight for row in weights for weight in row]
    if any(not isinstance(value, (int, float)) or not isfinite(value) for value in parameters):
        raise ValueError("Trained vision model artifact contains invalid numeric parameters.")
    if any(scale <= 0 for scale in scales):
        raise ValueError("Trained vision model feature scales must be positive.")

    vector, evidence = extract_image_features(image_path, tuple(artifact_features))
    normalized = [(value - means[index]) / scales[index] for index, value in enumerate(vector)]
    logits = [
        sum(weight * value for weight, value in zip(class_weights, normalized, strict=True)) + bias
        for class_weights, bias in zip(weights, biases, strict=True)
    ]
    probabilities = _softmax(logits)
    best = max(range(len(probabilities)), key=probabilities.__getitem__)
    return {
        "food_type": "unknown",
        "freshness": artifact["classes"][best],
        "confidence": round(probabilities[best], 4),
        "confidence_kind": "uncalibrated_model_score",
        "model_version": artifact["version"],
        "model_type": "trained",
        "visual_evidence": evidence,
        "validation_accuracy": artifact.get("validation_accuracy"),
    }


def predict_image(image_path: str, model_dir: str | None = None) -> dict:
    """Use a trained local artifact when present; otherwise disclose prototype fallback."""
    if model_dir is None:
        from app.core.config import settings

        model_dir = settings.MODEL_PATH
    artifact_path = Path(model_dir) / TRAINED_MODEL_FILENAME
    if artifact_path.is_file():
        return _predict_with_artifact(image_path, artifact_path)
    return heuristic_predict(image_path)
