#!/usr/bin/env python3
"""Train the local FreshSense vision classifier from a labeled CSV manifest."""

import argparse
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.ml.vision.training import train_vision_model


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="CSV with image_path,label,split columns")
    parser.add_argument(
        "--output",
        type=Path,
        default=BACKEND_DIR / "models" / "vision_model.candidate.json",
        help="Candidate artifact path; review metrics before promoting it to vision_model.json.",
    )
    parser.add_argument("--epochs", type=int, default=1000)
    parser.add_argument("--learning-rate", type=float, default=0.1)
    parser.add_argument("--l2", type=float, default=0.001)
    args = parser.parse_args()

    artifact = train_vision_model(
        args.manifest,
        args.output,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        l2=args.l2,
    )
    print(f"Saved {artifact['version']} to {args.output}")
    print(f"Validation accuracy: {artifact['validation_accuracy']:.1%}")
    print(f"Macro class recall: {artifact['validation_macro_recall']:.1%}")
    print("Class recall:")
    for label, recall in artifact["validation_class_recall"].items():
        print(f"  {label}: {recall:.1%}")
    print("Confusion matrix (actual rows, predicted columns):")
    for label, row in artifact["validation_confusion"].items():
        print(f"  {label}: {row}")


if __name__ == "__main__":
    main()
