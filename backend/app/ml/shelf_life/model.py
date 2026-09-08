"""Shelf-life model stub — MODEL TRAINING REQUIRED.

No trained weights exist in Phase 1. Shelf-life estimates must come from
OCR expiry dates via expiry_service, never from this stub.
"""

from app.ml.base import ModelInterface


class ShelfLifeStub(ModelInterface):
    name = "shelf_life"
    version = "shelf-life-v0.0-not-implemented"
    model_type = "not_implemented"

    def predict(self, inputs: dict) -> dict:
        return {
            "status": "MODEL TRAINING REQUIRED",
            "model_type": self.model_type,
            "message": "No shelf-life model trained yet. Use OCR expiry date + expiry_service.",
        }
