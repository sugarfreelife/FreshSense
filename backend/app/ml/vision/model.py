"""Vision model wrapper (trained local artifact or disclosed prototype fallback)."""

from app.ml.base import ModelInterface
from app.ml.vision.inference import predict_image


class VisionModel(ModelInterface):
    name = "vision"
    version = "adaptive-local-vision"
    model_type = "adaptive"

    def predict(self, inputs: str) -> dict:
        """inputs: path to image file."""
        return predict_image(inputs)
