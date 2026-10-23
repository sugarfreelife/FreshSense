#!/usr/bin/env python3
"""Evaluate end-to-end package category and expiry reads on labeled photos.

The input is a local CSV manifest. Images and labels stay out of version control.
Only held-out validation groups are scored; this script never trains a model.
"""

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.ocr.date_parser import extract_expiry_date  # noqa: E402
from app.ocr.product_parser import recognize_product  # noqa: E402
from app.ocr.service import extract_text_from_image  # noqa: E402

REQUIRED = {"image_path", "group_id", "split", "expected_category", "expected_expiry_date"}


def norm(value: str | None) -> str:
    return " ".join((value or "").strip().lower().split())


def evaluate(manifest: Path) -> dict:
    with manifest.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        missing = REQUIRED - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required CSV columns: {', '.join(sorted(missing))}")
        rows = list(reader)

    split_by_group: dict[str, str] = {}
    for line, row in enumerate(rows, start=2):
        group, split = (row.get("group_id") or "").strip(), (row.get("split") or "").strip().lower()
        if not group or split not in {"train", "validation"}:
            raise ValueError(f"Line {line}: group_id is required and split must be train or validation.")
        if group in split_by_group and split_by_group[group] != split:
            raise ValueError(f"Line {line}: group {group!r} crosses train and validation splits.")
        split_by_group[group] = split

    validation = [row for row in rows if row["split"].strip().lower() == "validation"]
    if not validation:
        raise ValueError("No validation rows found; keep training and validation groups separate.")

    category_total = category_correct = 0
    category_counts: Counter[str] = Counter()
    category_correct_by_class: Counter[str] = Counter()
    category_predicted_counts: Counter[str] = Counter()
    confusion: Counter[tuple[str, str]] = Counter()
    expiry_correct = expiry_predicted = expiry_expected = 0
    provider_counts: Counter[str] = Counter()
    results = []

    for index, row in enumerate(validation, start=1):
        image_text = (row.get("image_path") or "").strip()
        image_path = Path(image_text)
        if not image_path.is_absolute():
            image_path = manifest.parent / image_path
        if not image_path.is_file():
            raise ValueError(f"Validation row {index}: image does not exist: {image_path}")
        expected_category = norm(row.get("expected_category"))
        if not expected_category:
            raise ValueError(f"Validation row {index}: expected_category is required.")
        expected_expiry = (row.get("expected_expiry_date") or "").strip()
        text_result = extract_text_from_image(str(image_path))
        recognized = recognize_product(text_result.get("raw_text", ""))
        predicted_category = norm(recognized.get("category"))
        predicted_expiry = extract_expiry_date(text_result.get("raw_text", ""))["expiry_date"]
        predicted_expiry_text = predicted_expiry.isoformat() if predicted_expiry else ""

        category_total += 1
        category_counts[expected_category] += 1
        predicted_key = predicted_category or "(unrecognized)"
        category_predicted_counts[predicted_key] += 1
        confusion[(expected_category, predicted_key)] += 1
        is_category_correct = predicted_category == expected_category
        category_correct += int(is_category_correct)
        category_correct_by_class[expected_category] += int(is_category_correct)

        is_expiry_correct = predicted_expiry_text == expected_expiry and bool(expected_expiry)
        expiry_correct += int(is_expiry_correct)
        expiry_predicted += int(bool(predicted_expiry_text))
        expiry_expected += int(bool(expected_expiry))
        provider_counts[text_result.get("provider", "unknown")] += 1
        results.append({
            "image_path": image_text,
            "group_id": row["group_id"].strip(),
            "expected_category": expected_category,
            "predicted_category": predicted_category or None,
            "category_correct": is_category_correct,
            "expected_expiry_date": expected_expiry or None,
            "predicted_expiry_date": predicted_expiry_text or None,
            "expiry_exact_match": is_expiry_correct if expected_expiry else None,
            "ocr_provider": text_result.get("provider", "unknown"),
        })

    labels = sorted(category_counts)
    per_class = {}
    for label in labels:
        true_positive = confusion[(label, label)]
        precision = true_positive / category_predicted_counts[label] if category_predicted_counts[label] else 0.0
        recall = category_correct_by_class[label] / category_counts[label]
        f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
        per_class[label] = {"precision": precision, "recall": recall, "f1": f1, "support": category_counts[label]}
    macro_precision = sum(values["precision"] for values in per_class.values()) / len(per_class)
    macro_recall = sum(values["recall"] for values in per_class.values()) / len(per_class)
    macro_f1 = sum(values["f1"] for values in per_class.values()) / len(per_class)
    predicted_labels = sorted(set(labels) | set(category_predicted_counts))
    report = {
        "status": "measured",
        "validation_images": len(validation),
        "validation_groups": len({row["group_id"].strip() for row in validation}),
        "category_accuracy": category_correct / category_total,
        "category_macro_precision": macro_precision,
        "category_macro_recall": macro_recall,
        "category_macro_f1": macro_f1,
        "category_per_class": per_class,
        "category_confusion_matrix": {
            "labels": labels,
            "predicted_labels": predicted_labels,
            "rows": [[confusion[(actual, predicted)] for predicted in predicted_labels] for actual in labels],
        },
        "category_support": dict(sorted(category_counts.items())),
        "expiry_exact_match_rate": expiry_correct / expiry_expected if expiry_expected else None,
        "expiry_expected_dates": expiry_expected,
        "expiry_predicted_dates": expiry_predicted,
        "expiry_exact_precision": expiry_correct / expiry_predicted if expiry_predicted else None,
        "ocr_provider_counts": dict(sorted(provider_counts.items())),
        "scope_note": "Held-out package photos only; not a food-safety determination or a claim of generalization.",
        "items": results,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="CSV manifest; images remain local")
    parser.add_argument("--output", type=Path, help="Optional JSON report path")
    args = parser.parse_args()
    report = evaluate(args.manifest.resolve())
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
