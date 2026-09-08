from datetime import date, datetime

from pydantic import BaseModel


class VisionPredictionOut(BaseModel):
    food_type: str
    freshness: str
    confidence: float
    model_version: str
    model_type: str

    model_config = {"from_attributes": True}


class OCRResultOut(BaseModel):
    raw_text: str
    expiry_date: date | None = None
    date_detected: bool = False

    model_config = {"from_attributes": True}


class AssessmentOut(BaseModel):
    freshness: str
    confidence: float
    recommendation: str
    warnings: list[str] = []
    modalities_used: list[str] = []
    expiry_status: str
    days_remaining: int | None = None

    model_config = {"from_attributes": True}


class ScanOut(BaseModel):
    id: str
    image_path: str
    food_label: str | None = None
    created_at: datetime
    vision: VisionPredictionOut | None = None
    ocr: OCRResultOut | None = None
    assessment: AssessmentOut | None = None

    model_config = {"from_attributes": True}
