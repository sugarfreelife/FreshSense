import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.utils.time import utcnow_naive


def _uuid() -> str:
    return str(uuid.uuid4())


class FoodScan(Base):
    __tablename__ = "food_scans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    workspace_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("business_workspaces.id", ondelete="CASCADE"), nullable=True, index=True
    )
    tracked_item_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("tracked_items.id", ondelete="SET NULL"), nullable=True, index=True
    )
    image_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    food_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    product_recognition: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive, nullable=False)

    vision: Mapped["VisionPrediction | None"] = relationship(back_populates="scan", cascade="all, delete-orphan", uselist=False)
    ocr: Mapped["OCRResult | None"] = relationship(back_populates="scan", cascade="all, delete-orphan", uselist=False)
    assessment: Mapped["FinalAssessment | None"] = relationship(back_populates="scan", cascade="all, delete-orphan", uselist=False)
    sensor_readings: Mapped[list["SensorReading"]] = relationship(
        back_populates="scan", cascade="all, delete-orphan", lazy="selectin"
    )
    tracked_item: Mapped["TrackedItem | None"] = relationship(back_populates="scans", lazy="joined")
    workspace = relationship("BusinessWorkspace")


class TrackedItem(Base):
    __tablename__ = "tracked_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive, nullable=False)

    scans: Mapped[list[FoodScan]] = relationship(back_populates="tracked_item")


class VisionPrediction(Base):
    __tablename__ = "vision_predictions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    scan_id: Mapped[str] = mapped_column(String(36), ForeignKey("food_scans.id"), nullable=False, unique=True)
    food_type: Mapped[str] = mapped_column(String(255), default="unknown", nullable=False)
    freshness: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    model_version: Mapped[str] = mapped_column(String(100), nullable=False)
    model_type: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence_kind: Mapped[str] = mapped_column(String(50), default="heuristic_score", nullable=False)
    visual_evidence: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive, nullable=False)

    scan: Mapped[FoodScan] = relationship(back_populates="vision")


class OCRResult(Base):
    __tablename__ = "ocr_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    scan_id: Mapped[str] = mapped_column(String(36), ForeignKey("food_scans.id"), nullable=False, unique=True)
    raw_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_detected: Mapped[bool] = mapped_column(default=False, nullable=False)
    provider: Mapped[str] = mapped_column(String(50), default="unknown", nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    expiry_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    expiry_text: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive, nullable=False)

    scan: Mapped[FoodScan] = relationship(back_populates="ocr")


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    scan_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("food_scans.id"), nullable=True, index=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    gas_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(30), default="user_entered", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive, nullable=False)

    scan: Mapped[FoodScan | None] = relationship(back_populates="sensor_readings")


class FinalAssessment(Base):
    __tablename__ = "final_assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    scan_id: Mapped[str] = mapped_column(String(36), ForeignKey("food_scans.id"), nullable=False, unique=True)
    freshness: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    recommendation: Mapped[str] = mapped_column(String(100), nullable=False)
    warnings: Mapped[str] = mapped_column(Text, default="[]", nullable=False)  # JSON-encoded list
    modalities_used: Mapped[str] = mapped_column(Text, default="[]", nullable=False)  # JSON-encoded list
    expiry_status: Mapped[str] = mapped_column(String(50), nullable=False)
    days_remaining: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive, nullable=False)

    scan: Mapped[FoodScan] = relationship(back_populates="assessment")


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(100), nullable=False)
    model_type: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive, nullable=False)
