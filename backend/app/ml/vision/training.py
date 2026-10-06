"""Train the small interpretable freshness classifier from a labeled CSV manifest."""

import csv
import json
from datetime import datetime, timezone
from math import exp, isfinite, sqrt
from pathlib import Path

from app.ml.vision.features import FEATURE_NAMES, extract_image_features

CLASSES = ("fresh", "moderately_fresh", "spoiled")


def _softmax(logits: list[float]) -> list[float]:
    peak = max(logits)
    exponentials = [exp(value - peak) for value in logits]
    total = sum(exponentials)
    return [value / total for value in exponentials]


def _normalize(vector: list[float], means: list[float], scales: list[float]) -> list[float]:
    return [(value - means[i]) / scales[i] for i, value in enumerate(vector)]


def _read_manifest(manifest: Path) -> tuple[list[tuple[list[float], int]], list[tuple[list[float], int]]]:
    rows: dict[str, list[tuple[list[float], int]]] = {"train": [], "validation": []}
    groups: dict[str, set[str]] = {"train": set(), "validation": set()}
    with manifest.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        required = {"image_path", "split"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames) or not ({"label", "freshness_label"} & set(reader.fieldnames)):
            raise ValueError("Manifest needs image_path, label (or freshness_label), and split columns.")
        for line, row in enumerate(reader, start=2):
            split = (row.get("split") or "").strip().lower()
            label = (row.get("label") or row.get("freshness_label") or "").strip().lower().replace(" ", "_")
            image_path = Path((row.get("image_path") or "").strip())
            if split not in rows:
                raise ValueError(f"Line {line}: split must be 'train' or 'validation'.")
            if label not in CLASSES:
                raise ValueError(f"Line {line}: label must be one of {', '.join(CLASSES)}.")
            if not image_path.is_absolute():
                image_path = manifest.parent / image_path
            if not image_path.is_file():
                raise ValueError(f"Line {line}: image file does not exist: {image_path}")
            group = (row.get("group_id") or row.get("capture_session") or "").strip()
            if not group:
                raise ValueError(f"Line {line}: group_id (or capture_session) is required for leakage-safe validation.")
            groups[split].add(group)
            vector, _ = extract_image_features(str(image_path))
            rows[split].append((vector, CLASSES.index(label)))
    leaked_groups = groups["train"] & groups["validation"]
    if leaked_groups:
        raise ValueError("Capture groups must not appear in both train and validation splits.")
    if not rows["train"] or not rows["validation"]:
        raise ValueError("Manifest needs both training and validation examples.")
    for split, examples in rows.items():
        present = {label for _, label in examples}
        missing = [CLASSES[index] for index in range(len(CLASSES)) if index not in present]
        if missing:
            raise ValueError(f"{split} split is missing class(es): {', '.join(missing)}.")
    return rows["train"], rows["validation"]


def _fit(
    examples: list[tuple[list[float], int]],
    *,
    epochs: int,
    learning_rate: float,
    l2: float,
) -> tuple[list[float], list[float], list[list[float]], list[float]]:
    feature_count = len(FEATURE_NAMES)
    means = [sum(vector[i] for vector, _ in examples) / len(examples) for i in range(feature_count)]
    scales = []
    for i in range(feature_count):
        variance = sum((vector[i] - means[i]) ** 2 for vector, _ in examples) / len(examples)
        scales.append(sqrt(variance) or 1.0)
    normalized = [(_normalize(vector, means, scales), label) for vector, label in examples]
    weights = [[0.0] * feature_count for _ in CLASSES]
    biases = [0.0] * len(CLASSES)

    for _ in range(epochs):
        weight_gradients = [[0.0] * feature_count for _ in CLASSES]
        bias_gradients = [0.0] * len(CLASSES)
        for vector, label in normalized:
            probabilities = _softmax([
                sum(weight * value for weight, value in zip(class_weights, vector, strict=True)) + bias
                for class_weights, bias in zip(weights, biases, strict=True)
            ])
            for class_index, probability in enumerate(probabilities):
                error = probability - (1.0 if class_index == label else 0.0)
                bias_gradients[class_index] += error
                for feature_index, value in enumerate(vector):
                    weight_gradients[class_index][feature_index] += error * value
        count = len(normalized)
        for class_index in range(len(CLASSES)):
            biases[class_index] -= learning_rate * bias_gradients[class_index] / count
            for feature_index in range(feature_count):
                gradient = weight_gradients[class_index][feature_index] / count + l2 * weights[class_index][feature_index]
                weights[class_index][feature_index] -= learning_rate * gradient
    return means, scales, weights, biases


def train_vision_model(
    manifest_path: str | Path,
    output_path: str | Path,
    *,
    epochs: int = 1000,
    learning_rate: float = 0.1,
    l2: float = 0.001,
) -> dict:
    """Fit multinomial logistic regression and write a local JSON model artifact."""
    if (
        epochs < 1
        or not isfinite(learning_rate)
        or learning_rate <= 0
        or not isfinite(l2)
        or l2 < 0
    ):
        raise ValueError("epochs and learning_rate must be positive; l2 cannot be negative.")
    target = Path(output_path)
    if target.name == "vision_model.json":
        raise ValueError("Train to a candidate file, review its metrics, then promote it to vision_model.json.")
    manifest = Path(manifest_path).resolve()
    train, validation = _read_manifest(manifest)
    means, scales, weights, biases = _fit(
        train, epochs=epochs, learning_rate=learning_rate, l2=l2
    )
    confusion = {actual: {predicted: 0 for predicted in CLASSES} for actual in CLASSES}
    correct = 0
    for vector, actual in validation:
        normalized = _normalize(vector, means, scales)
        logits = [
            sum(weight * value for weight, value in zip(class_weights, normalized, strict=True)) + bias
            for class_weights, bias in zip(weights, biases, strict=True)
        ]
        predicted = max(range(len(logits)), key=logits.__getitem__)
        confusion[CLASSES[actual]][CLASSES[predicted]] += 1
        correct += predicted == actual
    class_recall = {
        actual: round(confusion[actual][actual] / sum(confusion[actual].values()), 4)
        for actual in CLASSES
    }

    trained_at = datetime.now(timezone.utc)
    artifact = {
        "schema_version": 1,
        "name": "freshsense-image-freshness-logistic",
        "version": f"vision-logistic-v2-{trained_at.strftime('%Y%m%dT%H%M%SZ')}",
        "model_type": "trained",
        "feature_schema": "color-histogram-spatial-v2",
        "classes": list(CLASSES),
        "feature_names": list(FEATURE_NAMES),
        "means": means,
        "scales": scales,
        "weights": weights,
        "bias": biases,
        "validation_accuracy": round(correct / len(validation), 4),
        "validation_confusion": confusion,
        "validation_class_recall": class_recall,
        "validation_macro_recall": round(sum(class_recall.values()) / len(class_recall), 4),
        "training_examples": len(train),
        "validation_examples": len(validation),
        "trained_at": trained_at.isoformat(),
        "score_note": "Softmax score is uncalibrated; validation accuracy is dataset-specific.",
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    temporary.replace(target)
    return artifact
