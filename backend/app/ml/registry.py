"""Registry of available models."""

from app.ml.base import ModelInterface
from app.ml.fusion.model import FusionStub
from app.ml.shelf_life.model import ShelfLifeStub
from app.ml.vision.model import VisionModel


def get_registry() -> dict[str, ModelInterface]:
    return {
        "vision": VisionModel(),
        "fusion": FusionStub(),
        "shelf_life": ShelfLifeStub(),
    }
