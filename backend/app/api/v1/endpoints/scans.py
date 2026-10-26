import asyncio
import json
import os
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Header, HTTPException, Query, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.core.rate_limit import limit_scan_requests
from app.ml.vision.inference import predict_image
from app.models.scan import FinalAssessment, FoodScan, OCRResult, SensorReading, TrackedItem, VisionPrediction
from app.models.user import User
from app.ocr.product_parser import recognize_product
from app.ocr.service import extract_text_from_image
from app.schemas.scan import ScanOut
from app.services import assessment_service
from app.services.passport_service import build_passport
from app.services.workspace_access import get_workspace_scope
from app.utils.time import utcnow_naive
from app.utils.files import MAX_FILE_SIZE_BYTES, validate_size
from app.utils.images import normalize_uploaded_image

router = APIRouter(prefix="/scans", tags=["scans"])
_BACKEND_DIR = Path(__file__).resolve().parents[4]


def _scan_query(db: Session, current: User, workspace_mode: str, workspace_id: str | None):
    scope = get_workspace_scope(db, current, workspace_mode, workspace_id)
    if scope[0] == "business":
        return (db.query(FoodScan).filter(FoodScan.workspace_id == scope[1]) if scope[1] else None), scope
    return db.query(FoodScan).filter(FoodScan.user_id == current.id, FoodScan.workspace_id.is_(None)), scope


def _upload_root() -> Path:
    root = Path(settings.UPLOAD_DIR)
    return root.resolve() if root.is_absolute() else (_BACKEND_DIR / root).resolve()


def _resolve_scan_image(stored_path: str) -> Path:
    path = Path(stored_path)
    if not path.is_absolute():
        path = _BACKEND_DIR / path
    return path.resolve()


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
            "provider": scan.ocr.provider,
            "confidence": scan.ocr.confidence,
            "expiry_label": scan.ocr.expiry_label,
              "expiry_text": scan.ocr.expiry_text,
            "created_at": scan.ocr.created_at,
        }
    product = recognize_product((ocr or {}).get("raw_text", ""), user_label=scan.food_label)
    sensor_row = max(scan.sensor_readings, key=lambda reading: reading.created_at, default=None)
    sensor = None
    if sensor_row:
        sensor = {
            "gas_value": sensor_row.gas_value,
            "temperature": sensor_row.temperature,
            "humidity": sensor_row.humidity,
            "source": sensor_row.source,
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
        product=product,
    )
    return {
        "id": scan.id,
        "image_url": f"/api/v1/scans/{scan.id}/image",
        # Tracked items remain user-private even when the scan is shared with a
        # business workspace, so do not expose a dangling private item link.
        "tracked_item_id": scan.tracked_item_id if scan.workspace_id is None else None,
        "tracked_item_label": scan.tracked_item.label if scan.tracked_item else None,
        "food_label": scan.food_label,
        "product": product,
        "notes": scan.notes,
        "created_at": scan.created_at,
        "vision": vision,
        "ocr": ocr,
        "sensor": sensor,
        "assessment": assessment,
        "passport": passport,
    }


@router.post(
    "",
    response_model=ScanOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(limit_scan_requests)],
)
async def create_scan(
    file: UploadFile,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
    workspace_mode: str = Header(default="personal", alias="X-Workspace-Mode"),
    workspace_id: str | None = Header(default=None, alias="X-Workspace-Id"),
    food_type: Annotated[str | None, Form(max_length=100)] = None,
    temperature_c: Annotated[float | None, Form(ge=-40, le=85)] = None,
    humidity_pct: Annotated[float | None, Form(ge=0, le=100)] = None,
    voc_index: Annotated[float | None, Form(ge=0, le=5000)] = None,
    sensor_source: Annotated[str, Form(pattern="^(user_entered|demo_estimate|mixed)$")] = "user_entered",
    notes: Annotated[str | None, Form(max_length=2000)] = None,
    tracked_item_id: Annotated[str | None, Form()] = None,
    new_item_name: Annotated[str | None, Form(max_length=100)] = None,
):
    scope = get_workspace_scope(db, current, workspace_mode, workspace_id)
    if scope[0] == "business" and scope[1] is None:
        raise HTTPException(status_code=409, detail="Create or select a business workspace before scanning stock")
    if scope[0] == "business" and (tracked_item_id or (new_item_name and new_item_name.strip())):
        raise HTTPException(status_code=400, detail="Tracked scan history is personal; business scans use the shared workspace history.")
    if tracked_item_id and new_item_name and new_item_name.strip():
        raise HTTPException(status_code=400, detail="Choose an existing item or name a new one, not both.")
    tracked_item = None
    if tracked_item_id:
        tracked_item = (
            db.query(TrackedItem)
            .filter(TrackedItem.id == tracked_item_id, TrackedItem.user_id == current.id)
            .first()
        )
        if tracked_item is None:
            raise HTTPException(status_code=404, detail="Tracked item not found")

    contents = await file.read(MAX_FILE_SIZE_BYTES + 1)
    if not validate_size(len(contents)):
        raise HTTPException(status_code=400, detail="File too large. Max 10MB.")

    upload_dir = _upload_root()
    upload_dir.mkdir(parents=True, exist_ok=True)
    upload_id = uuid.uuid4().hex
    safe_name = f"{upload_id}.jpg"
    dest_path = str(upload_dir / safe_name)
    original_path = upload_dir / f"{upload_id}.source"
    try:
        try:
            normalize_uploaded_image(contents, dest_path)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        with original_path.open("xb") as original_file:
            original_file.write(contents)

        vision, ocr = await asyncio.gather(
            run_in_threadpool(predict_image, dest_path),
            run_in_threadpool(extract_text_from_image, dest_path),
        )
        product = recognize_product(ocr.get("raw_text", ""), user_label=food_type)
        if product["category"] and product["source"] == "package_text":
            vision["food_type"] = product["category"]
        expiry_date = date.fromisoformat(ocr["expiry_date"]) if ocr.get("expiry_date") else None
        sensor_values = {
            "gas_value": voc_index,
            "temperature": temperature_c,
            "humidity": humidity_pct,
        }
        sensor = sensor_values if any(value is not None for value in sensor_values.values()) else None
        decision = assessment_service.assess_scan(
            vision=vision,
            sensor=sensor if sensor_source == "user_entered" else None,
            ocr=ocr,
            expiry_date=expiry_date,
        )

        if not tracked_item and new_item_name and new_item_name.strip():
            tracked_item = TrackedItem(user_id=current.id, label=new_item_name.strip())
            db.add(tracked_item)
            db.flush()

        scan = FoodScan(
            user_id=current.id,
            workspace_id=scope[1],
            tracked_item_id=tracked_item.id if tracked_item else None,
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
                provider=ocr.get("provider", "unknown"),
                confidence=ocr.get("confidence"),
                expiry_label=ocr.get("expiry_label"),
                  expiry_text=ocr.get("expiry_text"),
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
                    source=sensor_source,
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
        try:
            original_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


@router.post("/{scan_id}/reanalyze", response_model=ScanOut)
def reanalyze_scan(
    scan_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
    workspace_mode: str = Header(default="personal", alias="X-Workspace-Mode"),
    workspace_id: str | None = Header(default=None, alias="X-Workspace-Id"),
):
    """Re-read an existing scan photo so improved OCR can update its Passport."""
    query, scope = _scan_query(db, current, workspace_mode, workspace_id)
    if scope[0] == "business" and scope[1] is None:
        raise HTTPException(status_code=409, detail="Select a business workspace first")
    scan = query.filter(FoodScan.id == scan_id).first() if query is not None else None
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    image_path = _resolve_scan_image(scan.image_path)
    if not image_path.is_relative_to(_upload_root()) or not image_path.is_file():
        raise HTTPException(status_code=404, detail="The saved scan photo is no longer available")

    ocr = extract_text_from_image(str(image_path))
    recognized = recognize_product(ocr.get("raw_text", ""), user_label=scan.food_label)
    if scan.ocr is None:
        scan.ocr = OCRResult(scan_id=scan.id)
    scan.ocr.raw_text = ocr.get("raw_text", "")
    scan.ocr.expiry_date = date.fromisoformat(ocr["expiry_date"]) if ocr.get("expiry_date") else None
    scan.ocr.date_detected = bool(ocr.get("date_detected"))
    scan.ocr.provider = ocr.get("provider", "unknown")
    scan.ocr.confidence = ocr.get("confidence")
    scan.ocr.expiry_label = ocr.get("expiry_label")
    scan.ocr.expiry_text = ocr.get("expiry_text")
    scan.ocr.created_at = utcnow_naive()

    vision = None
    if scan.vision:
        vision = {
            "food_type": scan.vision.food_type,
            "freshness": scan.vision.freshness,
            "confidence": scan.vision.confidence,
            "model_type": scan.vision.model_type,
            "model_version": scan.vision.model_version,
            "confidence_kind": scan.vision.confidence_kind,
            "visual_evidence": json.loads(scan.vision.visual_evidence or "{}"),
        }
        if recognized.get("source") == "package_text" and recognized.get("category"):
            scan.vision.food_type = recognized["category"]
            vision["food_type"] = recognized["category"]

    sensor_row = max(scan.sensor_readings, key=lambda reading: reading.created_at, default=None)
    sensor = None
    if sensor_row:
        sensor = {
            "gas_value": sensor_row.gas_value,
            "temperature": sensor_row.temperature,
            "humidity": sensor_row.humidity,
            "source": sensor_row.source,
        }
    decision = assessment_service.assess_scan(
        vision=vision,
        sensor=sensor if (sensor_row and sensor_row.source == "user_entered") else None,
        ocr=ocr,
        expiry_date=scan.ocr.expiry_date,
    )
    if scan.assessment is None:
        scan.assessment = FinalAssessment(scan_id=scan.id)
    scan.assessment.freshness = decision["freshness"]
    scan.assessment.confidence = decision["confidence"]
    scan.assessment.recommendation = decision["recommendation"]
    scan.assessment.warnings = json.dumps(decision["warnings"])
    scan.assessment.modalities_used = json.dumps(decision["modalities_used"])
    scan.assessment.expiry_status = decision["expiry_status"]
    scan.assessment.days_remaining = decision["days_remaining"]
    scan.assessment.created_at = utcnow_naive()

    db.flush()
    response = _scan_to_out(scan)
    db.commit()
    return response


@router.get("", response_model=list[ScanOut])
def list_scans(
    response: Response,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    workspace_mode: str = Header(default="personal", alias="X-Workspace-Mode"),
    workspace_id: str | None = Header(default=None, alias="X-Workspace-Id"),
):
    query, scope = _scan_query(db, current, workspace_mode, workspace_id)
    if query is None:
        response.headers["X-Total-Count"] = "0"
        return []
    total = query.count()
    scans = query.order_by(FoodScan.created_at.desc()).offset(offset).limit(limit).all()
    response.headers["X-Total-Count"] = str(total)
    return [_scan_to_out(s) for s in scans]


@router.get("/items", tags=["tracked items"])
def list_tracked_items(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    rows = (
        db.query(TrackedItem, func.count(FoodScan.id), func.max(FoodScan.created_at))
        .join(FoodScan, FoodScan.tracked_item_id == TrackedItem.id)
        .filter(TrackedItem.user_id == current.id, FoodScan.user_id == current.id)
        .group_by(TrackedItem.id)
        .order_by(func.max(FoodScan.created_at).desc())
        .all()
    )
    return [
        {"id": item.id, "label": item.label, "scan_count": count, "last_scanned": last_scanned}
        for item, count, last_scanned in rows
    ]


@router.get("/items/{item_id}", tags=["tracked items"])
def get_tracked_item(item_id: str, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    item = db.query(TrackedItem).filter(TrackedItem.id == item_id, TrackedItem.user_id == current.id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Tracked item not found")
    scans = (
        db.query(FoodScan)
        .filter(FoodScan.tracked_item_id == item.id, FoodScan.user_id == current.id)
        .order_by(FoodScan.created_at.asc())
        .all()
    )
    return {"id": item.id, "label": item.label, "scans": [_scan_to_out(scan) for scan in scans]}


@router.get("/{scan_id}/image", include_in_schema=False)
def get_scan_image(
    scan_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
    workspace_mode: str = Header(default="personal", alias="X-Workspace-Mode"),
    workspace_id: str | None = Header(default=None, alias="X-Workspace-Id"),
):
    query, scope = _scan_query(db, current, workspace_mode, workspace_id)
    scan = query.filter(FoodScan.id == scan_id).first() if query is not None else None
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    upload_root = _upload_root()
    image_path = _resolve_scan_image(scan.image_path)
    if not image_path.is_relative_to(upload_root) or not image_path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(
        image_path,
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
    )


@router.get("/{scan_id}", response_model=ScanOut)
def get_scan(
    scan_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
    workspace_mode: str = Header(default="personal", alias="X-Workspace-Mode"),
    workspace_id: str | None = Header(default=None, alias="X-Workspace-Id"),
):
    query, scope = _scan_query(db, current, workspace_mode, workspace_id)
    scan = query.filter(FoodScan.id == scan_id).first() if query is not None else None
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return _scan_to_out(scan)


@router.delete("/{scan_id}")
def delete_scan(
    scan_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
    workspace_mode: str = Header(default="personal", alias="X-Workspace-Mode"),
    workspace_id: str | None = Header(default=None, alias="X-Workspace-Id"),
):
    query, scope = _scan_query(db, current, workspace_mode, workspace_id)
    if scope[0] == "business" and scope[1] is None:
        raise HTTPException(status_code=409, detail="Select a business workspace first")
    if scope[0] == "business" and scope[2] not in {"owner", "manager"}:
        raise HTTPException(status_code=403, detail="Only workspace owners and managers can delete shared scans")
    scan = query.filter(FoodScan.id == scan_id).first() if query is not None else None
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    image_path = _resolve_scan_image(scan.image_path) if scan.image_path else None
    db.delete(scan)
    db.commit()
    upload_root = _upload_root()
    if image_path and image_path.is_relative_to(upload_root):
        for path in (image_path, image_path.with_suffix(".source")):
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
    return {"message": "Scan deleted"}
