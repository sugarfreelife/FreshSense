import json
import os
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.ml.vision.inference import heuristic_predict
from app.models.scan import FinalAssessment, FoodScan, OCRResult, VisionPrediction
from app.models.user import User
from app.ocr.service import extract_text_from_image
from app.schemas.scan import ScanOut
from app.services import assessment_service
from app.utils.files import validate_extension, validate_mime, validate_size

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
        }
    ocr = None
    if scan.ocr:
        ocr = {
            "raw_text": scan.ocr.raw_text,
            "expiry_date": scan.ocr.expiry_date,
            "date_detected": scan.ocr.date_detected,
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
        }
    return {
        "id": scan.id,
        "image_path": scan.image_path,
        "food_label": scan.food_label,
        "created_at": scan.created_at,
        "vision": vision,
        "ocr": ocr,
        "assessment": assessment,
    }


@router.post("", response_model=ScanOut, status_code=status.HTTP_201_CREATED)
async def create_scan(
    file: UploadFile,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    filename = file.filename or "upload.jpg"
    if not validate_extension(filename):
        raise HTTPException(status_code=400, detail="Unsupported file extension. Use jpg, jpeg, png, or webp.")
    if not validate_mime(file.content_type):
        raise HTTPException(status_code=400, detail=f"Unsupported MIME type: {file.content_type}")
    contents = await file.read()
    if not validate_size(len(contents)):
        raise HTTPException(status_code=400, detail="File too large. Max 10MB.")

    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    ext = os.path.splitext(filename.lower())[1] or ".jpg"
    safe_name = f"{uuid.uuid4().hex}{ext}"
    dest_path = os.path.join(upload_dir, safe_name)
    with open(dest_path, "wb") as f:
        f.write(contents)

    # PIL verify (no fake validation)
    from app.utils.images import verify_image

    if not verify_image(dest_path):
        os.remove(dest_path)
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.")

    # Vision prototype (service/ML layer, not route logic)
    vision = heuristic_predict(dest_path)
    # OCR honest path (easyocr optional)
    ocr = extract_text_from_image(dest_path)
    expiry_date = None
    if ocr.get("expiry_date"):
        expiry_date = date.fromisoformat(ocr["expiry_date"])

    decision = assessment_service.assess_scan(vision=vision, sensor=None, ocr=ocr, expiry_date=expiry_date)

    scan = FoodScan(user_id=current.id, image_path=dest_path, food_label=vision.get("food_type"))
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
    db.commit()
    db.refresh(scan)
    return _scan_to_out(scan)


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
    try:
        if scan.image_path and os.path.exists(scan.image_path):
            os.remove(scan.image_path)
    except OSError:
        pass
    db.delete(scan)
    db.commit()
    return {"message": "Scan deleted"}
