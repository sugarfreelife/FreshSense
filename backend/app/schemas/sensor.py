from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class SensorReadingCreate(BaseModel):
    scan_id: str | None = None
    gas_value: float | None = Field(default=None, ge=0, le=5000)
    temperature: float | None = Field(default=None, ge=-40, le=85)
    humidity: float | None = Field(default=None, ge=0, le=100)

    @model_validator(mode="after")
    def require_sensor_value(self):
        if self.gas_value is None and self.temperature is None and self.humidity is None:
            raise ValueError("At least one sensor value is required")
        return self


class SensorReadingOut(BaseModel):
    id: str
    scan_id: str | None = None
    gas_value: float | None = None
    temperature: float | None = None
    humidity: float | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
