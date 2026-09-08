from pydantic import BaseModel


class ESP32Payload(BaseModel):
    gas_value: float | None = None
    temperature: float | None = None
    humidity: float | None = None
    scan_id: str | None = None
