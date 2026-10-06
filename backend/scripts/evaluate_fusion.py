#!/usr/bin/env python3
"""Compare appearance-only predictions with Freshness Passport evidence fusion."""

import argparse
import csv
import json
import random
import shutil
import sys
import tempfile
from collections import Counter
from datetime import date
from math import isfinite
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.ml.vision.inference import predict_image
from app.services.decision_service import decide
from app.core.enums import FreshnessEnum

CLASSES = [item.value for item in FreshnessEnum]
SENSOR_FIELDS = ("gas_value", "temperature", "humidity")


def optional_float(value: str, line: int, field: str) -> float | None:
    if not value.strip():
        return None
    try:
        number = float(value)
    except ValueError as exc:
        raise ValueError(f"Line {line}: {field} must be numeric.") from exc
    if not isfinite(number):
        raise ValueError(f"Line {line}: {field} must be finite.")
    return number


def metrics(actual: list[str], predicted: list[str]) -> dict:
    matrix = {label: {other: 0 for other in CLASSES} for label in CLASSES}
    for truth, guess in zip(actual, predicted, strict=True):
        matrix[truth][guess] += 1
    per_class = {}
    for label in CLASSES:
        tp = matrix[label][label]
        support = sum(matrix[label].values())
        predicted_count = sum(matrix[row][label] for row in CLASSES)
        precision = tp / predicted_count if predicted_count else 0.0
        recall = tp / support if support else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[label] = {"support": support, "precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4)}
    return {
        "examples": len(actual),
        "accuracy": round(sum(a == p for a, p in zip(actual, predicted, strict=True)) / len(actual), 4),
        "macro_precision": round(sum(v["precision"] for v in per_class.values()) / len(CLASSES), 4),
        "macro_recall": round(sum(v["recall"] for v in per_class.values()) / len(CLASSES), 4),
        "macro_f1": round(sum(v["f1"] for v in per_class.values()) / len(CLASSES), 4),
        "per_class": per_class,
        "confusion_matrix": matrix,
    }


def grouped_accuracy_interval(
    actual: list[str], vision: list[str], fused: list[str], groups: list[str], *, replicates: int = 2000
) -> dict:
    members: dict[str, list[int]] = {}
    for index, group in enumerate(groups):
        members.setdefault(group, []).append(index)
    if len(members) < 2:
        return {"confidence": 0.95, "lower": None, "upper": None, "groups": len(members)}
    randomizer = random.Random(42)
    group_names = list(members)
    differences = []
    for _ in range(replicates):
        sampled = [randomizer.choice(group_names) for _ in group_names]
        indices = [index for group in sampled for index in members[group]]
        vision_accuracy = sum(actual[i] == vision[i] for i in indices) / len(indices)
        fused_accuracy = sum(actual[i] == fused[i] for i in indices) / len(indices)
        differences.append(fused_accuracy - vision_accuracy)
    differences.sort()
    return {
        "confidence": 0.95,
        "lower": round(differences[int(0.025 * replicates)], 4),
        "upper": round(differences[int(0.975 * replicates)], 4),
        "groups": len(members),
        "method": "percentile cluster bootstrap by group_id (2000 replicates; seed 42)",
    }


def evaluate(manifest: Path, model_dir: Path, allow_prototype: bool = False) -> dict:
    rows = []
    groups: dict[str, set[str]] = {"train": set(), "validation": set()}
    with manifest.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        required = {"image_path", "freshness_label", "split", "group_id", "capture_date"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"Manifest requires columns: {', '.join(sorted(required))}.")
        for line, row in enumerate(reader, start=2):
            split = (row.get("split") or "").strip().lower()
            label = (row.get("freshness_label") or "").strip().lower().replace(" ", "_")
            group = (row.get("group_id") or "").strip()
            if split not in groups or label not in CLASSES or not group:
                raise ValueError(f"Line {line}: invalid split, freshness_label, or empty group_id.")
            image = Path((row.get("image_path") or "").strip())
            if not image.is_absolute():
                image = manifest.parent / image
            if not image.is_file():
                raise ValueError(f"Line {line}: image does not exist: {image}")
            try:
                captured = date.fromisoformat((row.get("capture_date") or "").strip())
                expiry_date = (row.get("expiry_date") or "").strip()
                expiry_date = date.fromisoformat(expiry_date) if expiry_date else None
            except ValueError as exc:
                raise ValueError(f"Line {line}: capture_date/expiry_date must use YYYY-MM-DD.") from exc
            sensor_values = {field: optional_float(row.get(field, ""), line, field) for field in SENSOR_FIELDS}
            has_secondary = expiry_date is not None or any(value is not None for value in sensor_values.values())
            groups[split].add(group)
            if split == "validation":
                rows.append((line, image, label, captured, expiry_date, sensor_values, has_secondary, group))
    if groups["train"] & groups["validation"]:
        raise ValueError("Capture groups must not overlap between train and validation splits.")
    if not rows:
        raise ValueError("No validation examples found.")
    if not any(row[6] for row in rows):
        raise ValueError("Validation examples need paired sensor or expiry evidence to compare fusion.")

    actual, vision_only, fused = [], [], []
    model_types = Counter()
    groups_for_validation = []
    for line, image, label, captured, expiry_date, sensor, _, group in rows:
        vision = predict_image(str(image), model_dir=str(model_dir))
        model_types[vision["model_type"]] += 1
        if vision["model_type"] != "trained" and not allow_prototype:
            raise ValueError("A trained vision_model.json is required; pass --allow-prototype only for pipeline smoke checks.")
        common = {"vision": vision, "reference_date": captured}
        image_assessment = decide(**common)
        sensor_payload = sensor if any(value is not None for value in sensor.values()) else None
        fused_assessment = decide(
            **common,
            sensor=sensor_payload,
            expiry_date=expiry_date,
        )
        actual.append(label)
        vision_only.append(image_assessment["freshness"])
        fused.append(fused_assessment["freshness"])
        groups_for_validation.append(group)

    vision_metrics = metrics(actual, vision_only)
    fusion_metrics = metrics(actual, fused)
    return {
        "evaluation": "held-out grouped comparison; predictions are not food-safety determinations",
        "validation_examples": len(rows),
        "model_types": dict(model_types),
        "appearance_only": vision_metrics,
        "passport_fusion": fusion_metrics,
        "fusion_minus_vision_accuracy": round(fusion_metrics["accuracy"] - vision_metrics["accuracy"], 4),
        "fusion_minus_vision_accuracy_cluster_bootstrap_95pct": grouped_accuracy_interval(
            actual, vision_only, fused, groups_for_validation
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    model_source = parser.add_mutually_exclusive_group()
    model_source.add_argument("--model-dir", type=Path, default=BACKEND_DIR / "models")
    model_source.add_argument(
        "--model-artifact",
        type=Path,
        help="Evaluate a candidate JSON artifact without activating it in the application.",
    )
    parser.add_argument("--output", type=Path, help="Optional JSON report path.")
    parser.add_argument("--allow-prototype", action="store_true", help="Allow prototype predictions for pipeline smoke checks; metrics are not trained-model results.")
    args = parser.parse_args()
    if args.model_artifact:
        artifact = args.model_artifact.resolve()
        if not artifact.is_file():
            parser.error(f"model artifact does not exist: {artifact}")
        with tempfile.TemporaryDirectory(prefix="freshsense-eval-") as temporary:
            shutil.copyfile(artifact, Path(temporary) / "vision_model.json")
            report = evaluate(args.manifest.resolve(), Path(temporary), args.allow_prototype)
    else:
        report = evaluate(args.manifest.resolve(), args.model_dir.resolve(), args.allow_prototype)
    rendered = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
