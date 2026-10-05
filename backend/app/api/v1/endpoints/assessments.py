import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.scan import FinalAssessment, FoodScan, SensorReading
from app.models.user import User
from app.schemas.assessment import AssessmentRequest, AssessmentResponse
from app.services import assessment_service

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.post("", response_model=AssessmentResponse)
def create_assessment(
    payload: AssessmentRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    vision = None
    if payload.vision_freshness:
        confidence = payload.vision_confidence
        vision = {"freshness": payload.vision_freshness, "confidence": 0.5 if confidence is None else confidence}
    sensor = None
    if payload.gas_value is not None or payload.temperature is not None or payload.humidity is not None:
        sensor = {
            "gas_value": payload.gas_value,
            "temperature": payload.temperature,
            "humidity": payload.humidity,
        }
    ocr = None
    if payload.expiry_date:
        ocr = {"expiry_date": payload.expiry_date, "date_detected": True, "raw_text": ""}

    scan = None
    if payload.scan_id:
        scan = (
            db.query(FoodScan)
            .filter(FoodScan.id == payload.scan_id, FoodScan.user_id == current.id)
            .first()
        )
        if scan is None:
            raise HTTPException(status_code=404, detail="Scan not found")
        if vision is None and scan.vision is not None:
            vision = {
                "freshness": scan.vision.freshness,
                "confidence": scan.vision.confidence,
                "food_type": scan.vision.food_type,
                "model_type": scan.vision.model_type,
            }
        if ocr is None and scan.ocr is not None:
            ocr = {
                "expiry_date": scan.ocr.expiry_date,
                "date_detected": scan.ocr.date_detected,
                "raw_text": scan.ocr.raw_text,
            }
        stored_sensor = (
            db.query(SensorReading)
            .filter(SensorReading.scan_id == scan.id, SensorReading.user_id == current.id)
            .order_by(SensorReading.created_at.desc())
            .first()
        )
        if stored_sensor is not None:
            sensor = {
                "gas_value": stored_sensor.gas_value,
                "temperature": stored_sensor.temperature,
                "humidity": stored_sensor.humidity,
            } | {key: value for key, value in (sensor or {}).items() if value is not None}

    result = assessment_service.assess_scan(vision=vision, sensor=sensor, ocr=ocr, expiry_date=payload.expiry_date)
    result.pop("evidence", None)
    if scan is not None:
        assessment = scan.assessment
        if assessment is None:
            assessment = FinalAssessment(scan_id=scan.id)
            db.add(assessment)
        assessment.freshness = result["freshness"]
        assessment.confidence = result["confidence"]
        assessment.recommendation = result["recommendation"]
        assessment.warnings = json.dumps(result["warnings"])
        assessment.modalities_used = json.dumps(result["modalities_used"])
        assessment.expiry_status = result["expiry_status"]
        assessment.days_remaining = result["days_remaining"]
        db.commit()
    return result


@router.get("/{scan_id}", response_model=AssessmentResponse)
def get_assessment(scan_id: str, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    scan = db.query(FoodScan).filter(FoodScan.id == scan_id, FoodScan.user_id == current.id).first()
    if not scan or not scan.assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    a = scan.assessment
    return {
        "freshness": a.freshness,
        "confidence": a.confidence,
        "recommendation": a.recommendation,
        "warnings": json.loads(a.warnings or "[]"),
        "modalities_used": json.loads(a.modalities_used or "[]"),
        "expiry_status": a.expiry_status,
        "days_remaining": a.days_remaining,
    }
