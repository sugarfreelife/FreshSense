"""Model interface shared by all ML modules."""

from abc import ABC, abstractmethod
from typing import Any


class ModelInterface(ABC):
    name: str = "base"
    version: str = "v0.0"
    model_type: str = "not_implemented"  # trained | prototype | adaptive | not_implemented

    @abstractmethod
    def predict(self, inputs: Any) -> dict:
        raise NotImplementedError

    def info(self) -> dict:
        return {"name": self.name, "version": self.version, "model_type": self.model_type}
