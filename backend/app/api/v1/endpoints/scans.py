import json
import os
import uuid
from datetime import date
from pathlib import Path
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.ml.vision.inference import predict_image
from app.models.scan import FinalAssessment, FoodScan, OCRResult, SensorReading, VisionPrediction
from app.models.user import User
from app.ocr.service import extract_text_from_image
from app.schemas.scan import ScanOut
from app.services import assessment_service
from app.services.passport_service import build_passport
from app.utils.files import MAX_FILE_SIZE_BYTES, validate_extension, validate_mime, validate_size

router = APIRouter(prefix="/scans", tags=["scans"])


def _scan_to_out(scan: FoodScan) -> dict:
    vision = None
    if scan.vision:
        vision = {
            "food_type": scan.vision.food_type,
            "freshness": scan.vision.freshness,
            "confidence": scan.vision.confidence,
            "model_version": scan.vision.model_version,
            "model_type": scan.vision.model_type,
            "confidence_kind": scan.vision.confidence_kind,
            "visual_evidence": json.loads(scan.vision.visual_evidence or "{}"),
            "created_at": scan.vision.created_at,
        }
    ocr = None
    if scan.ocr:
        ocr = {
            "raw_text": scan.ocr.raw_text,
            "expiry_date": scan.ocr.expiry_date,
            "date_detected": scan.ocr.date_detected,
            "created_at": scan.ocr.created_at,
        }
    sensor_row = max(scan.sensor_readings, key=lambda reading: reading.created_at, default=None)
    sensor = None
    if sensor_row:
        sensor = {
            "gas_value": sensor_row.gas_value,
            "temperature": sensor_row.temperature,
            "humidity": sensor_row.humidity,
            "created_at": sensor_row.created_at,
        }
    assessment = None
    if scan.assessment:
        assessment = {
            "freshness": scan.assessment.freshness,
            "confidence": scan.assessment.confidence,
            "recommendation": scan.assessment.recommendation,
            "warnings": json.loads(scan.assessment.warnings or "[]"),
            "modalities_used": json.loads(scan.assessment.modalities_used or "[]"),
            "expiry_status": scan.assessment.expiry_status,
            "days_remaining": scan.assessment.days_remaining,
            "created_at": scan.assessment.created_at,
        }
    passport = build_passport(
        created_at=scan.created_at,
        vision=vision,
        ocr=ocr,
        sensor=sensor,
        assessment=assessment,
    )
    return {
        "id": scan.id,
        "image_url": f"/uploads/{quote(Path(scan.image_path).name)}",
        "food_label": scan.food_label,
        "notes": scan.notes,
        "created_at": scan.created_at,
        "vision": vision,
        "ocr": ocr,
        "sensor": sensor,
        "assessment": assessment,
        "passport": passport,
    }


@router.post("", response_model=ScanOut, status_code=status.HTTP_201_CREATED)
async def create_scan(
    file: UploadFile,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
    food_type: Annotated[str | None, Form(max_length=100)] = None,
    temperature_c: Annotated[float | None, Form(ge=-40, le=85)] = None,
    humidity_pct: Annotated[float | None, Form(ge=0, le=100)] = None,
    voc_index: Annotated[float | None, Form(ge=0, le=5000)] = None,
    notes: Annotated[str | None, Form(max_length=2000)] = None,
):
    filename = file.filename or "upload.jpg"
    if not validate_extension(filename):
        raise HTTPException(status_code=400, detail="Unsupported file extension. Use jpg, jpeg, png, or webp.")
    if not validate_mime(file.content_type):
        raise HTTPException(status_code=400, detail=f"Unsupported MIME type: {file.content_type}")
    contents = await file.read(MAX_FILE_SIZE_BYTES + 1)
    if not validate_size(len(contents)):
        raise HTTPException(status_code=400, detail="File too large. Max 10MB.")

    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    ext = os.path.splitext(filename.lower())[1] or ".jpg"
    safe_name = f"{uuid.uuid4().hex}{ext}"
    dest_path = os.path.join(upload_dir, safe_name)
    try:
        with open(dest_path, "xb") as f:
            f.write(contents)

        from app.utils.images import verify_image

        if not verify_image(dest_path):
            raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.")

        vision = predict_image(dest_path)
        ocr = extract_text_from_image(dest_path)
        expiry_date = date.fromisoformat(ocr["expiry_date"]) if ocr.get("expiry_date") else None
        sensor_values = {
            "gas_value": voc_index,
            "temperature": temperature_c,
            "humidity": humidity_pct,
        }
        sensor = sensor_values if any(value is not None for value in sensor_values.values()) else None
        decision = assessment_service.assess_scan(
            vision=vision, sensor=sensor, ocr=ocr, expiry_date=expiry_date
        )

        scan = FoodScan(
            user_id=current.id,
            image_path=dest_path,
            food_label=food_type.strip() if food_type and food_type.strip() else None,
            notes=notes.strip() if notes and notes.strip() else None,
        )
        db.add(scan)
        db.flush()
        db.add(
            VisionPrediction(
                scan_id=scan.id,
                food_type=vision.get("food_type", "unknown"),
                freshness=vision["freshness"],
                confidence=vision["confidence"],
                model_version=vision["model_version"],
                model_type=vision["model_type"],
                confidence_kind=vision.get("confidence_kind", "heuristic_score"),
                visual_evidence=json.dumps(vision.get("visual_evidence", {})),
            )
        )
        db.add(
            OCRResult(
                scan_id=scan.id,
                raw_text=ocr.get("raw_text", ""),
                expiry_date=expiry_date,
                date_detected=ocr.get("date_detected", False),
            )
        )
        if sensor is not None:
            db.add(
                SensorReading(
                    scan_id=scan.id,
                    user_id=current.id,
                    gas_value=sensor["gas_value"],
                    temperature=sensor["temperature"],
                    humidity=sensor["humidity"],
                )
            )
        db.add(
            FinalAssessment(
                scan_id=scan.id,
                freshness=decision["freshness"],
                confidence=decision["confidence"],
                recommendation=decision["recommendation"],
                warnings=json.dumps(decision["warnings"]),
                modalities_used=json.dumps(decision["modalities_used"]),
                expiry_status=decision["expiry_status"],
                days_remaining=decision["days_remaining"],
            )
        )
        db.flush()
        db.refresh(scan)
        response = _scan_to_out(scan)
        db.commit()
        return response
    except Exception:
        db.rollback()
        try:
            os.remove(dest_path)
        except OSError:
            pass
        raise


@router.get("", response_model=list[ScanOut])
def list_scans(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    scans = db.query(FoodScan).filter(FoodScan.user_id == current.id).order_by(FoodScan.created_at.desc()).all()
    return [_scan_to_out(s) for s in scans]


@router.get("/{scan_id}", response_model=ScanOut)
def get_scan(scan_id: str, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    scan = db.query(FoodScan).filter(FoodScan.id == scan_id, FoodScan.user_id == current.id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return _scan_to_out(scan)


@router.delete("/{scan_id}")
def delete_scan(scan_id: str, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    scan = db.query(FoodScan).filter(FoodScan.id == scan_id, FoodScan.user_id == current.id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    image_path = scan.image_path
    db.query(SensorReading).filter(SensorReading.scan_id == scan.id).delete(synchronize_session=False)
    db.delete(scan)
    db.commit()
    try:
        if image_path and os.path.exists(image_path):
            os.remove(image_path)
    except OSError:
        pass
    return {"message": "Scan deleted"}
