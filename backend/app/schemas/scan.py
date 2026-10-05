from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class VisionPredictionOut(BaseModel):
    food_type: str
    freshness: str
    confidence: float
    model_version: str
    model_type: str
    confidence_kind: str = "heuristic_score"
    visual_evidence: dict[str, float] = Field(default_factory=dict)
    created_at: datetime

    model_config = {"from_attributes": True}


class OCRResultOut(BaseModel):
    raw_text: str
    expiry_date: date | None = None
    date_detected: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class AssessmentOut(BaseModel):
    freshness: str
    confidence: float
    recommendation: str
    warnings: list[str] = Field(default_factory=list)
    modalities_used: list[str] = Field(default_factory=list)
    expiry_status: str
    days_remaining: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SensorEvidenceOut(BaseModel):
    gas_value: float | None = None
    temperature: float | None = None
    humidity: float | None = None
    created_at: datetime


class PassportEvidenceOut(BaseModel):
    key: Literal["vision", "expiry", "sensor"]
    title: str
    state: Literal["used", "warning", "missing", "context"]
    observation: str
    explanation: str


class PassportEventOut(BaseModel):
    key: str
    title: str
    state: Literal["complete", "warning", "missing"]
    detail: str
    occurred_at: datetime | None = None


class FreshnessPassportOut(BaseModel):
    summary: str
    explanation: str
    evidence: list[PassportEvidenceOut] = Field(default_factory=list)
    timeline: list[PassportEventOut] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class ScanOut(BaseModel):
    id: str
    image_url: str
    food_label: str | None = None
    notes: str | None = None
    created_at: datetime
    vision: VisionPredictionOut | None = None
    ocr: OCRResultOut | None = None
    sensor: SensorEvidenceOut | None = None
    assessment: AssessmentOut | None = None
    passport: FreshnessPassportOut

    model_config = {"from_attributes": True}
