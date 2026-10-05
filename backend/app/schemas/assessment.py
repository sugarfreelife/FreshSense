from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class AssessmentRequest(BaseModel):
    scan_id: str | None = None
    vision_freshness: Literal["fresh", "moderately_fresh", "spoiled"] | None = None
    vision_confidence: float | None = Field(default=None, ge=0, le=1)
    gas_value: float | None = Field(default=None, ge=0, le=5000)
    temperature: float | None = Field(default=None, ge=-40, le=85)
    humidity: float | None = Field(default=None, ge=0, le=100)
    expiry_date: date | None = None


class AssessmentResponse(BaseModel):
    freshness: str
    confidence: float
    recommendation: str
    warnings: list[str] = Field(default_factory=list)
    modalities_used: list[str] = Field(default_factory=list)
    expiry_status: str
    days_remaining: int | None = None
