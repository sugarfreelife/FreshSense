"""Phase-2 fusion model stub — NOT IMPLEMENTED.

Planned: learned multimodal fusion of vision + VOC + OCR features.
Phase 1 uses the deterministic rules in app/services/decision_service.py.
"""

from app.ml.base import ModelInterface


class FusionStub(ModelInterface):
    name = "fusion"
    version = "fusion-v0.0-not-implemented"
    model_type = "not_implemented"

    def predict(self, inputs: dict) -> dict:
        return {
            "status": "NOT_IMPLEMENTED",
            "model_type": self.model_type,
            "message": "Fusion model is Phase 2 work. Use decision_service rules in Phase 1.",
        }
