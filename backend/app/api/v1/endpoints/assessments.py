from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.scan import FoodScan
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
    _ = db, current  # stateless rule engine; db reserved for future persistence
    vision = None
    if payload.vision_freshness:
        vision = {"freshness": payload.vision_freshness, "confidence": payload.vision_confidence or 0.5}
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
    result = assessment_service.assess_scan(vision=vision, sensor=sensor, ocr=ocr, expiry_date=payload.expiry_date)
    result.pop("evidence", None)
    return result


@router.get("/{scan_id}", response_model=AssessmentResponse)
def get_assessment(scan_id: str, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    import json

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
