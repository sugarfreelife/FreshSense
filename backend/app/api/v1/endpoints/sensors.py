from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.scan import FoodScan, SensorReading
from app.models.user import User
from app.schemas.sensor import SensorReadingCreate, SensorReadingOut
from app.sensors.service import validate_reading
from app.services.workspace_access import get_workspace_scope

router = APIRouter(prefix="/sensors", tags=["sensors"])


@router.post("/readings", response_model=SensorReadingOut, status_code=201)
def create_reading(
    payload: SensorReadingCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
    workspace_mode: str = Header(default="personal", alias="X-Workspace-Mode"),
    workspace_id: str | None = Header(default=None, alias="X-Workspace-Id"),
):
    scope = get_workspace_scope(db, current, workspace_mode, workspace_id)
    ok, errors = validate_reading(payload.gas_value, payload.temperature, payload.humidity)
    if not ok:
        raise HTTPException(status_code=400, detail="; ".join(errors))
    if payload.scan_id is not None:
        scan_query = db.query(FoodScan).filter(FoodScan.id == payload.scan_id)
        if scope[0] == "business":
            scan_query = scan_query.filter(FoodScan.workspace_id == scope[1]) if scope[1] else scan_query.filter(FoodScan.id == "")
        else:
            scan_query = scan_query.filter(FoodScan.user_id == current.id, FoodScan.workspace_id.is_(None))
        scan = scan_query.first()
        if scan is None:
            raise HTTPException(status_code=404, detail="Scan not found")
    reading = SensorReading(
        scan_id=payload.scan_id,
        user_id=current.id,
        gas_value=payload.gas_value,
        temperature=payload.temperature,
        humidity=payload.humidity,
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


@router.get("/readings", response_model=list[SensorReadingOut])
def list_readings(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
    workspace_mode: str = Header(default="personal", alias="X-Workspace-Mode"),
    workspace_id: str | None = Header(default=None, alias="X-Workspace-Id"),
):
    scope = get_workspace_scope(db, current, workspace_mode, workspace_id)
    query = db.query(SensorReading).outerjoin(FoodScan, SensorReading.scan_id == FoodScan.id)
    if scope[0] == "business":
        query = query.filter(FoodScan.workspace_id == scope[1]) if scope[1] else query.filter(FoodScan.id == "")
    else:
        query = query.filter(
            SensorReading.user_id == current.id,
            or_(SensorReading.scan_id.is_(None), FoodScan.workspace_id.is_(None)),
        )
    return query.order_by(SensorReading.created_at.desc()).all()
