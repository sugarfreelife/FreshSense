"""Sensor providers.

Expected ESP32+MQ+DHT22 payload (documented for firmware team):
    {"gas_value": <float ppm-ish 0..5000>, "temperature": <float C>, "humidity": <float %>}
"""

import random
import time
from abc import ABC, abstractmethod


class SensorProvider(ABC):
    name: str = "base"

    @abstractmethod
    def read(self) -> dict:
        raise NotImplementedError


class MockSensorProvider(SensorProvider):
    name = "mock"

    def read(self) -> dict:
        return {
            "gas_value": round(random.uniform(50, 300), 2),
            "temperature": round(random.uniform(20, 28), 2),
            "humidity": round(random.uniform(35, 65), 2),
            "timestamp": time.time(),
            "provider": self.name,
        }


class ESP32Provider(SensorProvider):
    """Stub for real ESP32 hardware (Phase 2).

    Firmware should POST JSON:
        {"gas_value": float, "temperature": float, "humidity": float}
    to POST /api/v1/sensors/readings.
    """

    name = "esp32"

    def read(self) -> dict:
        return {
            "gas_value": None,
            "temperature": None,
            "humidity": None,
            "provider": self.name,
            "message": "No live ESP32 connected. POST readings from firmware instead.",
        }
