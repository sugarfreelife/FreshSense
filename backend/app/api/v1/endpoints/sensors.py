from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.scan import SensorReading
from app.models.user import User
from app.schemas.sensor import SensorReadingCreate, SensorReadingOut
from app.sensors.service import validate_reading

router = APIRouter(prefix="/sensors", tags=["sensors"])


@router.post("/readings", response_model=SensorReadingOut, status_code=201)
def create_reading(
    payload: SensorReadingCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    ok, errors = validate_reading(payload.gas_value, payload.temperature, payload.humidity)
    if not ok:
        raise HTTPException(status_code=400, detail="; ".join(errors))
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
def list_readings(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    return (
        db.query(SensorReading)
        .filter(SensorReading.user_id == current.id)
        .order_by(SensorReading.created_at.desc())
        .all()
    )
