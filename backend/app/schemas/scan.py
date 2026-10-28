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
    provider: str = "unknown"
    confidence: float | None = None
    expiry_label: str | None = None
    expiry_text: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductAlternativeOut(BaseModel):
    name: str
    category: str | None = None
    similarity: float


class LabelDetailsOut(BaseModel):
    package_size: str | None = None
    ingredients: str | None = None
    allergens: str | None = None
    storage_instructions: str | None = None
    nutrition_text: str | None = None


class ProductRecognitionOut(BaseModel):
    category: str | None = None
    product_name: str | None = None
    confidence: float | None = None
    evidence: list[str] = Field(default_factory=list)
    source: Literal["package_text", "image_model", "image_and_text", "user_label", "unrecognized"] = "unrecognized"
    status: str = "unrecognized"
    confidence_kind: str | None = None
    model: str | None = None
    packaging: str | None = None
    alternatives: list[ProductAlternativeOut] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    label_details: LabelDetailsOut | None = None


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
    source: Literal["user_entered", "demo_estimate", "mixed", "legacy"] = "legacy"
    created_at: datetime


class PassportEvidenceOut(BaseModel):
    key: Literal["vision", "product", "expiry", "sensor"]
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


class PassportConflictOut(BaseModel):
    key: Literal["vision_sensor", "vision_expiry"]
    title: str
    detail: str


class PassportNextActionOut(BaseModel):
    key: Literal[
        "resolve_conflict",
        "confirm_date",
        "identify_product",
        "replace_demo_values",
        "repeat_observation",
        "review_result",
    ]
    title: str
    detail: str
    action_label: str
    target: Literal["pantry", "scan"]


class FreshnessPassportOut(BaseModel):
    summary: str
    explanation: str
    evidence: list[PassportEvidenceOut] = Field(default_factory=list)
    timeline: list[PassportEventOut] = Field(default_factory=list)
    conflicts: list[PassportConflictOut] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    next_action: PassportNextActionOut


class ScanOut(BaseModel):
    id: str
    tracked_item_id: str | None = None
    tracked_item_label: str | None = None
    image_url: str
    food_label: str | None = None
    notes: str | None = None
    product: ProductRecognitionOut = Field(default_factory=ProductRecognitionOut)
    created_at: datetime
    vision: VisionPredictionOut | None = None
    ocr: OCRResultOut | None = None
    sensor: SensorEvidenceOut | None = None
    assessment: AssessmentOut | None = None
    passport: FreshnessPassportOut

    model_config = {"from_attributes": True}
