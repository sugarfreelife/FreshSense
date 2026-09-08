"""Registry of available models (Phase 1: vision prototype only)."""

from app.ml.base import ModelInterface
from app.ml.fusion.model import FusionStub
from app.ml.shelf_life.model import ShelfLifeStub
from app.ml.vision.model import VisionPrototype


def get_registry() -> dict[str, ModelInterface]:
    return {
        "vision": VisionPrototype(),
        "fusion": FusionStub(),
        "shelf_life": ShelfLifeStub(),
    }
