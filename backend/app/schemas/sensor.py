from datetime import datetime

from pydantic import BaseModel


class SensorReadingCreate(BaseModel):
    scan_id: str | None = None
    gas_value: float | None = None
    temperature: float | None = None
    humidity: float | None = None


class SensorReadingOut(BaseModel):
    id: str
    scan_id: str | None = None
    gas_value: float | None = None
    temperature: float | None = None
    humidity: float | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
