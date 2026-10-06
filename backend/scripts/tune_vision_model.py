#!/usr/bin/env python3
"""Tune the image classifier using group-held-out folds inside training data."""

import argparse
import csv
import hashlib
import json
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.ml.vision.features import FEATURE_NAMES, extract_image_features
from app.ml.vision.training import CLASSES, _fit, _normalize


CONFIGS = (
    {"epochs": 1000, "learning_rate": 0.1, "l2": 0.001},
    {"epochs": 1500, "learning_rate": 0.1, "l2": 0.001},
    {"epochs": 1000, "learning_rate": 0.2, "l2": 0.0001},
    {"epochs": 500, "learning_rate": 0.2, "l2": 0.0001},
    {"epochs": 1000, "learning_rate": 0.1, "l2": 0.0001},
)


def read_data(manifest: Path):
    rows = {"train": [], "validation": []}
    groups = {"train": set(), "validation": set()}
    digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
    with manifest.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        required = {"image_path", "split", "group_id", "source"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames) or not (
            {"label", "freshness_label"} & set(reader.fieldnames)
        ):
            raise ValueError("Manifest needs image_path, label (or freshness_label), split, group_id, and source.")
        for line, row in enumerate(reader, start=2):
            split = (row.get("split") or "").strip().lower()
            label = (row.get("label") or row.get("freshness_label") or "").strip().lower().replace(" ", "_")
            group = (row.get("group_id") or "").strip()
            source_name = (row.get("source") or "").strip().lower()
            image_path = Path((row.get("image_path") or "").strip())
            if split not in rows or label not in CLASSES or not group or not source_name:
                raise ValueError(f"Line {line}: invalid split, label, group_id, or source.")
            if not image_path.is_absolute():
                image_path = manifest.parent / image_path
            if not image_path.is_file():
                raise ValueError(f"Line {line}: image does not exist: {image_path}")
            vector, _ = extract_image_features(str(image_path))
            item = (vector, CLASSES.index(label), group, source_name)
            rows[split].append(item)
            groups[split].add(group)

    overlap = groups["train"] & groups["validation"]
    if overlap:
        raise ValueError(f"Training and validation groups overlap: {', '.join(sorted(overlap)[:5])}")
    for split, examples in rows.items():
        present = {label for _, label, _, _ in examples}
        missing = set(range(len(CLASSES))) - present
        if missing:
            raise ValueError(f"{split} is missing classes: {', '.join(CLASSES[index] for index in sorted(missing))}")
    return rows, digest


def make_group_folds(examples, folds: int, seed: int):
    """Build deterministic folds by AgriFreshNET capture group and label."""
    by_class: dict[int, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    group_labels: dict[str, set[int]] = defaultdict(set)
    for item in examples:
        _, label, group, source = item
        if source != "agrifreshnet":
            continue
        by_class[label][group].append(item)
        group_labels[group].add(label)
    if any(len(labels) != 1 for labels in group_labels.values()):
        raise ValueError("An AgriFreshNET group has conflicting labels; resolve it before tuning.")
    if not group_labels:
        raise ValueError("No AgriFreshNET training groups are available for tuning.")
    if min(len(groups) for groups in by_class.values()) < folds:
        raise ValueError(f"At least {folds} AgriFreshNET groups per class are required.")

    assignments: dict[str, int] = {}
    for label in range(len(CLASSES)):
        items = list(by_class[label].items())
        random.Random(seed + label).shuffle(items)
        items.sort(key=lambda pair: -len(pair[1]))
        fold_sizes = [0] * folds
        for group, group_rows in items:
            smallest = min(fold_sizes)
            choices = [index for index, size in enumerate(fold_sizes) if size == smallest]
            fold = choices[0]
            assignments[group] = fold
            fold_sizes[fold] += len(group_rows)

    validation_folds = []
    for fold in range(folds):
        validation_groups = {group for group, assigned in assignments.items() if assigned == fold}
        validation = [item for item in examples if item[3] == "agrifreshnet" and item[2] in validation_groups]
        training = [item for item in examples if item[3] == "agrifreshnet" and item[2] not in validation_groups]
        labels = {label for _, label, _, _ in validation}
        if labels != set(range(len(CLASSES))):
            raise ValueError(f"Cross-validation fold {fold + 1} does not contain every class.")
        validation_folds.append((training, validation, len(validation_groups)))
    return validation_folds


def macro_recall(actual: list[int], predicted: list[int]) -> float:
    recalls = []
    for label in range(len(CLASSES)):
        support = sum(value == label for value in actual)
        recalls.append(sum(a == label and p == label for a, p in zip(actual, predicted, strict=True)) / support)
    return sum(recalls) / len(recalls)


def predict(examples, parameters) -> list[int]:
    means, scales, weights, biases = parameters
    output = []
    for vector, _, _, _ in examples:
        normalized = _normalize(vector, means, scales)
        logits = [
            sum(weight * value for weight, value in zip(class_weights, normalized, strict=True)) + bias
            for class_weights, bias in zip(weights, biases, strict=True)
        ]
        output.append(max(range(len(logits)), key=logits.__getitem__))
    return output


def score_report(actual: list[int], predicted: list[int]) -> dict:
    confusion = {label: {other: 0 for other in CLASSES} for label in CLASSES}
    for truth, guess in zip(actual, predicted, strict=True):
        confusion[CLASSES[truth]][CLASSES[guess]] += 1
    recalls = {
        label: confusion[label][label] / sum(confusion[label].values())
        for label in CLASSES
    }
    return {
        "examples": len(actual),
        "accuracy": round(sum(a == p for a, p in zip(actual, predicted, strict=True)) / len(actual), 4),
        "macro_recall": round(sum(recalls.values()) / len(CLASSES), 4),
        "class_recall": {label: round(value, 4) for label, value in recalls.items()},
        "confusion_matrix": confusion,
    }


def tune(manifest: Path, output: Path, *, folds: int = 3, seed: int = 42) -> dict:
    print("Extracting image features and checking manifest integrity...", flush=True)
    rows, manifest_sha256 = read_data(manifest.resolve())
    agri_training = [item for item in rows["train"] if item[3] == "agrifreshnet"]
    fold_data = make_group_folds(agri_training, folds, seed)
    print(f"Running {len(CONFIGS)} configurations across {folds} grouped folds...", flush=True)
    search = []
    for config_index, config in enumerate(CONFIGS, start=1):
        fold_scores = []
        fold_sizes = []
        for training, validation, group_count in fold_data:
            parameters = _fit(
                [(vector, label) for vector, label, _, _ in training],
                epochs=config["epochs"],
                learning_rate=config["learning_rate"],
                l2=config["l2"],
            )
            predicted = predict(validation, parameters)
            actual = [label for _, label, _, _ in validation]
            fold_scores.append(macro_recall(actual, predicted))
            fold_sizes.append({"examples": len(validation), "groups": group_count})
        search.append({
            **config,
            "fold_macro_recall": [round(score, 4) for score in fold_scores],
            "mean_macro_recall": round(sum(fold_scores) / len(fold_scores), 4),
            "fold_sizes": fold_sizes,
        })
        print(
            f"  {config_index}/{len(CONFIGS)} {config}: grouped CV macro recall "
            f"{search[-1]['mean_macro_recall']:.1%}",
            flush=True,
        )

    best = max(search, key=lambda result: (result["mean_macro_recall"], result["learning_rate"], -result["l2"]))
    train = rows["train"]
    validation = rows["validation"]
    parameters = _fit(
        [(vector, label) for vector, label, _, _ in train],
        epochs=best["epochs"],
        learning_rate=best["learning_rate"],
        l2=best["l2"],
    )
    actual = [label for _, label, _, _ in validation]
    final_report = score_report(actual, predict(validation, parameters))
    means, scales, weights, biases = parameters
    now = datetime.now(timezone.utc)
    artifact = {
        "schema_version": 1,
        "name": "freshsense-image-freshness-logistic",
        "version": f"vision-logistic-v2-tuned-{now.strftime('%Y%m%dT%H%M%SZ')}",
        "model_type": "trained",
        "feature_schema": "color-histogram-spatial-v2",
        "classes": list(CLASSES),
        "feature_names": list(FEATURE_NAMES),
        "means": means,
        "scales": scales,
        "weights": weights,
        "bias": biases,
        "validation_accuracy": final_report["accuracy"],
        "validation_confusion": final_report["confusion_matrix"],
        "validation_class_recall": final_report["class_recall"],
        "validation_macro_recall": final_report["macro_recall"],
        "training_examples": len(train),
        "validation_examples": len(validation),
        "trained_at": now.isoformat(),
        "score_note": "Small dataset-specific grouped tuning result; softmax score is uncalibrated and not a safety determination.",
        "tuning": {
            "selection_metric": "mean macro recall",
            "selection_data": "AgriFreshNET training groups only; FruQ-DB excluded because source-video groups are unavailable",
            "folds": folds,
            "seed": seed,
            "manifest_sha256": manifest_sha256,
            "selected_config": {key: best[key] for key in ("epochs", "learning_rate", "l2")},
            "selected_cv_mean_macro_recall": best["mean_macro_recall"],
            "search": search,
            "final_validation": final_report,
            "validation_note": "The fixed AgriFreshNET validation split was used once after config selection; the public sample is a convenience subset, not a representative benchmark.",
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    temporary.replace(output)
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, default=BACKEND_DIR / "models" / "vision_model.tuned.candidate.json")
    parser.add_argument("--folds", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.folds < 2:
        parser.error("--folds must be at least 2")
    artifact = tune(args.manifest, args.output, folds=args.folds, seed=args.seed)
    print(f"Saved tuned candidate to {args.output}")
    print(f"Selected config: {artifact['tuning']['selected_config']}")
    print(f"Grouped CV macro recall: {artifact['tuning']['selected_cv_mean_macro_recall']:.1%}")
    print(f"Final validation accuracy: {artifact['validation_accuracy']:.1%}")
    print(f"Final validation macro recall: {artifact['validation_macro_recall']:.1%}")
    print(f"Class recall: {artifact['validation_class_recall']}")


if __name__ == "__main__":
    main()
