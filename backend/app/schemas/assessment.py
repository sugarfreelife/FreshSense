from datetime import date

from pydantic import BaseModel


class AssessmentRequest(BaseModel):
    scan_id: str | None = None
    vision_freshness: str | None = None
    vision_confidence: float | None = None
    gas_value: float | None = None
    temperature: float | None = None
    humidity: float | None = None
    expiry_date: date | None = None


class AssessmentResponse(BaseModel):
    freshness: str
    confidence: float
    recommendation: str
    warnings: list[str] = []
    modalities_used: list[str] = []
    expiry_status: str
    days_remaining: int | None = None
