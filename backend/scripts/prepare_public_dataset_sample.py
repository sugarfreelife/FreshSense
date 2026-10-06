#!/usr/bin/env python3
"""Fetch a deterministic, grouped image sample from public Freshness datasets.

Only selected ZIP member ranges are fetched. This avoids downloading whole
archives while preserving class labels and original-image groups for the
AgriFreshNET augmentations. FruQ-DB has no per-video IDs in its merged archive,
so its sample is training-only and is never used for validation metrics.
"""

import argparse
import csv
import hashlib
import random
import re
import struct
import time
import zlib
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "data" / "metadata" / "labels.csv"
IMAGE_ROOT = ROOT / "data" / "extracted" / "public_sample"

SOURCES = {
    "agrifreshnet": {
        "url": "https://prod-dcd-datasets-public-files-eu-west-1.s3.eu-west-1.amazonaws.com/efa1a3b3-3239-48f1-aecc-dfc5e16ffd2d",
        "size": 347_828_971,
        "classes": 24,
        "window": 120,
    },
    "fruq_db": {
        "url": "https://zenodo.org/api/records/7224690/files/FruQ-DB.zip/content",
        "size": 241_067_015,
        "classes": 3,
        "window": 250,
    },
}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


@dataclass(frozen=True)
class Member:
    name: str
    compressed_size: int
    uncompressed_size: int
    compression: int
    crc32: int
    local_offset: int


def fetch_range(url: str, start: int, end: int) -> bytes:
    expected = end - start + 1
    for attempt in range(5):
        request = Request(url, headers={"Range": f"bytes={start}-{end}"})
        try:
            with urlopen(request, timeout=120) as response:
                if response.status != 206:
                    raise RuntimeError(f"Server ignored byte range {start}-{end} (HTTP {response.status}).")
                body = response.read()
            if len(body) == expected:
                return body
        except (HTTPError, OSError, TimeoutError) as error:
            if attempt == 4:
                raise RuntimeError(f"Archive range request failed for bytes {start}-{end}: {error}.") from error
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Short range response for bytes {start}-{end}; expected {expected} bytes.")


def read_directory(source: dict) -> list[Member]:
    tail_size = min(65_536, source["size"])
    tail_offset = source["size"] - tail_size
    tail = fetch_range(source["url"], tail_offset, source["size"] - 1)
    eocd_offset = tail.rfind(b"PK\x05\x06")
    if eocd_offset < 0:
        raise RuntimeError("ZIP end-of-directory record is missing.")
    record = struct.unpack_from("<4s4H2LH", tail, eocd_offset)
    _, disk, directory_disk, disk_entries, entry_count, directory_size, directory_offset, comment_size = record
    if disk or directory_disk or disk_entries != entry_count or directory_offset == 0xFFFFFFFF:
        raise RuntimeError("Multi-disk and ZIP64 archives are not supported by this sampler.")
    if eocd_offset + 22 + comment_size > len(tail):
        raise RuntimeError("Truncated ZIP end-of-directory record.")
    directory = fetch_range(source["url"], directory_offset, directory_offset + directory_size - 1)
    members = []
    cursor = 0
    for _ in range(entry_count):
        values = struct.unpack_from("<4s6H3L5H2L", directory, cursor)
        if values[0] != b"PK\x01\x02":
            raise RuntimeError(f"Invalid ZIP central-directory entry at byte {cursor}.")
        name_size, extra_size, comment_size = values[10:13]
        name_start = cursor + 46
        name = directory[name_start:name_start + name_size].decode("utf-8", "replace")
        members.append(Member(name, values[8], values[9], values[4], values[7], values[16]))
        cursor = name_start + name_size + extra_size + comment_size
    if cursor != len(directory):
        raise RuntimeError("ZIP central-directory size does not match its entries.")
    return members


def class_label(name: str, dataset: str) -> str | None:
    parts = name.replace("\\", "/").split("/")
    if dataset == "fruq_db":
        folder = parts[1].casefold() if len(parts) > 1 else ""
        return {"fresh": "fresh", "mild": "moderately_fresh", "rotten": "spoiled"}.get(folder)
    folder = parts[1].casefold() if len(parts) > 2 else ""
    if "rotten" in folder:
        return "spoiled"
    if "semi" in folder or "moderate" in folder:
        return "moderately_fresh"
    if "fresh" in folder:
        return "fresh"
    return None


def original_group(name: str) -> str:
    filename = name.rsplit("/", 1)[-1]
    filename = re.sub(r"^aug_\d+_", "", filename, flags=re.IGNORECASE)
    return filename.casefold()


def agri_fruit(name: str) -> str:
    folder = name.replace("\\", "/").split("/")[1].casefold()
    for fruit in ("bittermelon", "cucumber", "eggplant", "pineapple", "banana", "orange", "papaya", "tomato"):
        if fruit in folder:
            return fruit
    raise RuntimeError(f"Could not identify the produce group for {name}.")


def label_windows(members: list[Member], dataset: str, window_size: int, seed: int) -> list[tuple[str, list[Member]]]:
    folders: dict[str, list[Member]] = {}
    for member in members:
        if Path(member.name).suffix.casefold() not in IMAGE_SUFFIXES:
            continue
        label = class_label(member.name, dataset)
        if label is None:
            continue
        folder = member.name.split("/")[1]
        folders.setdefault(folder, []).append(member)

    windows = []
    for folder in sorted(folders):
        images = sorted(folders[folder], key=lambda member: member.local_offset)
        count = min(window_size, len(images))
        chooser = random.Random(f"{seed}:{dataset}:{folder}")
        start = chooser.randrange(len(images) - count + 1)
        windows.append((folder, images[start:start + count]))
    return windows


def inflate_member(data: bytes, window_offset: int, member: Member) -> bytes:
    local = member.local_offset - window_offset
    if local < 0 or data[local:local + 4] != b"PK\x03\x04":
        raise RuntimeError(f"Missing ZIP local header for {member.name}.")
    name_size, extra_size = struct.unpack_from("<HH", data, local + 26)
    begin = local + 30 + name_size + extra_size
    compressed = data[begin:begin + member.compressed_size]
    if len(compressed) != member.compressed_size:
        raise RuntimeError(f"Truncated image data for {member.name}.")
    if member.compression == 0:
        image = compressed
    elif member.compression == 8:
        image = zlib.decompress(compressed, -zlib.MAX_WBITS)
    else:
        raise RuntimeError(f"Unsupported ZIP compression method {member.compression}.")
    if len(image) != member.uncompressed_size or zlib.crc32(image) != member.crc32:
        raise RuntimeError(f"ZIP integrity check failed for {member.name}.")
    return image


def stable_validation(group: str, seed: int) -> bool:
    digest = hashlib.sha256(f"{seed}:{group}".encode()).digest()
    return int.from_bytes(digest[:4], "big") % 5 == 0


def extract_source(dataset: str, seed: int) -> list[dict[str, str]]:
    source = SOURCES[dataset]
    members = read_directory(source)
    windows = label_windows(members, dataset, source["window"], seed)
    rows: list[dict[str, str]] = []

    def output_for(member: Member) -> Path:
        relative_path = Path(dataset) / hashlib.sha256(member.name.encode()).hexdigest()[:16]
        return (IMAGE_ROOT / relative_path).with_suffix(Path(member.name).suffix.casefold())

    def fetch_window(window: tuple[str, list[Member]]) -> tuple[str, list[Member], int, bytes]:
        folder, images = window
        unique_images = []
        seen: set[str] = set()
        for member in images:
            key = original_group(member.name) if dataset == "agrifreshnet" else member.name
            if key not in seen:
                seen.add(key)
                unique_images.append(member)
        if all(output_for(member).is_file() for member in unique_images):
            return folder, images, images[0].local_offset, b""
        first = images[0]
        last = images[-1]
        start = first.local_offset
        final_header = fetch_range(source["url"], last.local_offset, last.local_offset + 29)
        final_name_size, final_extra_size = struct.unpack_from("<HH", final_header, 26)
        end = last.local_offset + 30 + final_name_size + final_extra_size + last.compressed_size - 1
        body = fetch_range(source["url"], start, end)
        return folder, images, start, body

    # Keep a few long-lived workers so the remote hosts are not flooded with connections.
    with ThreadPoolExecutor(max_workers=4) as pool:
        fetched = list(pool.map(fetch_window, windows))

    for folder, images, start, body in fetched:
        label = class_label(images[0].name, dataset)
        seen_groups: set[str] = set()
        for member in images:
            group_name = original_group(member.name) if dataset == "agrifreshnet" else member.name
            if group_name in seen_groups:
                continue
            seen_groups.add(group_name)
            group_id = (
                f"agrifreshnet:{agri_fruit(member.name)}:{group_name}"
                if dataset == "agrifreshnet"
                else f"fruq_db:train_only:{label}"
            )
            split = "validation" if dataset == "agrifreshnet" and stable_validation(group_id, seed) else "train"
            output = output_for(member)
            if not output.is_file():
                image_bytes = inflate_member(body, start, member)
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(image_bytes)
            relative_path = output.relative_to(IMAGE_ROOT)
            rows.append({
                "image_path": (Path("../extracted/public_sample") / relative_path).as_posix(),
                "freshness_label": label,
                "split": split,
                "group_id": group_id,
                "source": dataset,
            })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    args = parser.parse_args()

    rows = extract_source("agrifreshnet", args.seed) + extract_source("fruq_db", args.seed)
    labels_per_group: dict[str, set[str]] = {}
    for row in rows:
        labels_per_group.setdefault(row["group_id"], set()).add(row["freshness_label"])
    conflicting_groups = {group for group, labels in labels_per_group.items() if len(labels) > 1}
    rows = [row for row in rows if row["group_id"] not in conflicting_groups]
    split_labels = {split: {row["freshness_label"] for row in rows if row["split"] == split} for split in ("train", "validation")}
    required = {"fresh", "moderately_fresh", "spoiled"}
    if any(split_labels[split] != required for split in ("train", "validation")):
        counts = {split: {label: sum(row["split"] == split and row["freshness_label"] == label for row in rows) for label in sorted(required)} for split in ("train", "validation")}
        raise RuntimeError(f"The grouped sample must contain all three labels in both splits; found {counts}.")

    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    with args.manifest.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=("image_path", "freshness_label", "split", "group_id", "source"))
        writer.writeheader()
        writer.writerows(rows)
    counts = {split: {label: sum(row["split"] == split and row["freshness_label"] == label for row in rows) for label in sorted(required)} for split in ("train", "validation")}
    print(f"Wrote {len(rows)} images to {args.manifest}")
    print(f"Counts: {counts}")
    print(f"Excluded {len(conflicting_groups)} groups with conflicting labels.")
    print("FruQ-DB is training-only because the merged archive does not identify source videos.")


if __name__ == "__main__":
    main()
