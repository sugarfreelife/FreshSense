"""OCR provider interface."""

from abc import ABC, abstractmethod


class OCRProvider(ABC):
    name: str = "base"

    @abstractmethod
    def extract_text(self, image_path: str) -> dict:
        """Return {raw_text, provider}. Must never fabricate dates."""
        raise NotImplementedError
