"""Vision prototype model wrapper."""

from app.ml.base import ModelInterface
from app.ml.vision.inference import MODEL_VERSION, heuristic_predict


class VisionPrototype(ModelInterface):
    name = "vision"
    version = MODEL_VERSION
    model_type = "prototype"

    def predict(self, inputs: str) -> dict:
        """inputs: path to image file."""
        return heuristic_predict(inputs)
