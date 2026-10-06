#!/usr/bin/env python3
"""Extract the raw Fresh and Rotten Fruits Parquet shards as train-only images."""

import argparse
import csv
import hashlib
import io
from pathlib import Path

import pyarrow.parquet as parquet
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
DOWNLOADS = ROOT / "data" / "downloads"
IMAGES = ROOT / "data" / "extracted" / "fresh_rotten"
MANIFEST = ROOT / "data" / "metadata" / "labels.csv"
LABELS = {0: "fresh", 1: "spoiled"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--downloads", type=Path, default=DOWNLOADS)
    args = parser.parse_args()

    shards = sorted(args.downloads.glob("fresh_rotten_raw_*.parquet"))
    if len(shards) != 4:
        raise SystemExit(f"Expected all four raw Parquet shards in {args.downloads}; found {len(shards)}.")
    rows: list[dict[str, str]] = []
    for shard in shards:
        reader = parquet.ParquetFile(shard)
        if not {"image", "label", "fruit_type"}.issubset(reader.schema_arrow.names):
            raise ValueError(f"Unexpected columns in {shard.name}: {reader.schema_arrow.names}")
        shard_index = int(shard.stem.rsplit("_", 1)[1])
        for batch in reader.iter_batches(batch_size=64, columns=["image", "label", "fruit_type"]):
            for record in batch.to_pylist():
                label_id = record["label"]
                if label_id not in LABELS:
                    raise ValueError(f"Unexpected source label ID {label_id!r} in {shard.name}.")
                image = record["image"]
                payload = image.get("bytes") if image else None
                if not payload:
                    raise ValueError(f"Missing image bytes in {shard.name}.")
                # Decode before writing so corrupt or mislabeled non-image rows fail early.
                with Image.open(io.BytesIO(payload)) as decoded:
                    decoded.verify()
                    suffix = (decoded.format or "JPEG").lower()
                fingerprint = hashlib.sha256(payload).hexdigest()
                relative = Path("fresh_rotten") / f"{fingerprint}.{suffix}"
                destination = IMAGES / relative.name
                if not destination.exists():
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(payload)
                fruit = (record.get("fruit_type") or "unknown").strip().lower()
                rows.append({
                    "image_path": (Path("../extracted") / relative).as_posix(),
                    "freshness_label": LABELS[label_id],
                    "split": "train",
                    "group_id": f"fresh_rotten:train_only:{shard_index}:{fingerprint}",
                    "source": f"fresh_rotten:{fruit}",
                })

    existing: list[dict[str, str]] = []
    if args.manifest.is_file():
        with args.manifest.open(newline="", encoding="utf-8-sig") as stream:
            reader = csv.DictReader(stream)
            fields = reader.fieldnames or []
            required = {"image_path", "freshness_label", "split", "group_id", "source"}
            if not required.issubset(fields):
                raise ValueError(f"Existing manifest lacks required columns: {sorted(required - set(fields))}")
            existing = list(reader)
    known = {row["group_id"] for row in existing}
    added = [row for row in rows if row["group_id"] not in known]
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    fields = ("image_path", "freshness_label", "split", "group_id", "source")
    temporary = args.manifest.with_suffix(args.manifest.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(existing)
        writer.writerows(added)
    temporary.replace(args.manifest)
    counts = {label: sum(row["freshness_label"] == label for row in rows) for label in LABELS.values()}
    print(f"Extracted {len(rows)} raw images; class counts: {counts}.")
    print(f"Added {len(added)} fresh_rotten training rows to {args.manifest}.")
    print("All imported rows are training-only; no validation labels or rows were changed.")


if __name__ == "__main__":
    main()
