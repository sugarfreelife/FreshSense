#!/usr/bin/env python3
"""Validate a labeled, paired image/sensor/expiry CSV before fusion evaluation."""

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

CLASSES = {"fresh", "moderately_fresh", "spoiled"}
SPLITS = {"train", "validation"}
READINGS = {
    "gas_value": ("gas_unit", "gas_sensor_model"),
    "temperature": ("temperature_unit", "temperature_sensor_model"),
    "humidity": ("humidity_unit", "humidity_sensor_model"),
}
REQUIRED = {
    "image_id", "image_path", "food_type", "freshness_label", "capture_date",
    "capture_time_utc", "expiry_date", "expiry_type", "split", "group_id",
    "source", "conditions", "label_protocol_version", "review_status",
    "reviewer_ids", "adjudicator_id", "reference_method", "calibration_record_id",
    *(field for pair in READINGS.items() for field in pair[1]),
    *READINGS,
}


def fail(line: int, message: str) -> ValueError:
    return ValueError(f"Line {line}: {message}")


def optional_number(value: str, line: int, field: str) -> float | None:
    if not value.strip():
        return None
    try:
        number = float(value)
    except ValueError as exc:
        raise fail(line, f"{field} must be numeric.") from exc
    if not math.isfinite(number):
        raise fail(line, f"{field} must be finite.")
    return number


def validate(manifest: Path) -> dict:
    split_groups: dict[str, set[str]] = {split: set() for split in SPLITS}
    class_counts = {split: Counter() for split in SPLITS}
    group_labels: dict[str, set[str]] = defaultdict(set)
    seen_images: set[str] = set()
    row_counts = Counter()

    with manifest.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames or not REQUIRED.issubset(reader.fieldnames):
            missing = sorted(REQUIRED - set(reader.fieldnames or []))
            raise ValueError(f"Manifest is missing required columns: {', '.join(missing)}")

        for line, row in enumerate(reader, start=2):
            image_id = (row.get("image_id") or "").strip()
            image_text = (row.get("image_path") or "").strip()
            food_type = (row.get("food_type") or "").strip()
            label = (row.get("freshness_label") or "").strip().lower().replace(" ", "_")
            split = (row.get("split") or "").strip().lower()
            group = (row.get("group_id") or "").strip()
            if not all((image_id, image_text, food_type, group)):
                raise fail(line, "image_id, image_path, food_type, and group_id are required.")
            if image_id in seen_images:
                raise fail(line, f"duplicate image_id {image_id!r}.")
            seen_images.add(image_id)
            image = Path(image_text)
            if not image.is_absolute():
                image = manifest.parent / image
            if not image.is_file():
                raise fail(line, f"image does not exist: {image}")
            if label not in CLASSES or split not in SPLITS:
                raise fail(line, "freshness_label or split is invalid.")
            if (row.get("review_status") or "").strip().lower() != "adjudicated":
                raise fail(line, "review_status must be adjudicated before evaluation.")
            if not all((row.get(field) or "").strip() for field in (
                "source", "conditions", "label_protocol_version", "adjudicator_id", "reference_method"
            )):
                raise fail(line, "source, conditions, protocol version, adjudicator, and reference method are required.")
            reviewers = {value.strip() for value in (row.get("reviewer_ids") or "").split(";") if value.strip()}
            if len(reviewers) < 2:
                raise fail(line, "reviewer_ids must list at least two pseudonymous IDs separated by semicolons.")

            try:
                capture_day = date.fromisoformat((row.get("capture_date") or "").strip())
            except ValueError as exc:
                raise fail(line, "capture_date must use YYYY-MM-DD.") from exc
            try:
                captured_at = datetime.fromisoformat((row.get("capture_time_utc") or "").strip().replace("Z", "+00:00"))
            except ValueError as exc:
                raise fail(line, "capture_time_utc must be ISO 8601 with a UTC offset.") from exc
            if captured_at.tzinfo is None or captured_at.utcoffset() != timedelta(0):
                raise fail(line, "capture_time_utc must be expressed in UTC.")
            if captured_at.date() != capture_day:
                raise fail(line, "capture_date must match the UTC date in capture_time_utc.")

            expiry_text = (row.get("expiry_date") or "").strip()
            expiry_type = (row.get("expiry_type") or "").strip().lower()
            if expiry_text:
                try:
                    date.fromisoformat(expiry_text)
                except ValueError as exc:
                    raise fail(line, "expiry_date must use YYYY-MM-DD.") from exc
                if expiry_type not in {"use_by", "best_before", "expiry", "other"}:
                    raise fail(line, "expiry_type must be use_by, best_before, expiry, or other when expiry_date is present.")
            elif expiry_type:
                raise fail(line, "expiry_type must be empty when expiry_date is empty.")

            has_sensor = False
            for field, (unit_field, model_field) in READINGS.items():
                value = optional_number(row.get(field) or "", line, field)
                if value is None:
                    continue
                has_sensor = True
                if not (row.get(unit_field) or "").strip() or not (row.get(model_field) or "").strip():
                    raise fail(line, f"{unit_field} and {model_field} are required when {field} is recorded.")
                if field == "gas_value" and not 0 <= value <= 5000:
                    raise fail(line, "gas_value must be between 0 and 5000.")
                if field == "humidity" and not 0 <= value <= 100:
                    raise fail(line, "humidity must be between 0 and 100 percent.")
            if has_sensor and not (row.get("calibration_record_id") or "").strip():
                raise fail(line, "calibration_record_id is required when sensor readings are present.")
            if not has_sensor and not expiry_text:
                raise fail(line, "each row needs at least one measured sensor value or an observed expiry date.")

            split_groups[split].add(group)
            class_counts[split][label] += 1
            group_labels[group].add(label)
            row_counts[split] += 1

    if not row_counts:
        raise ValueError("Manifest has a header but no data rows.")
    overlap = split_groups["train"] & split_groups["validation"]
    if overlap:
        raise ValueError(f"Groups occur in both splits: {', '.join(sorted(overlap)[:5])}")
    for split in SPLITS:
        missing = CLASSES - set(class_counts[split])
        if missing:
            raise ValueError(f"{split} is missing classes: {', '.join(sorted(missing))}")

    return {
        "manifest": str(manifest),
        "rows": dict(row_counts),
        "groups": {split: len(groups) for split, groups in split_groups.items()},
        "classes": {split: dict(class_counts[split]) for split in SPLITS},
        "groups_with_multiple_labels": sum(len(labels) > 1 for labels in group_labels.values()),
        "status": "valid for paired fusion evaluation",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    report = validate(args.manifest.resolve())
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
