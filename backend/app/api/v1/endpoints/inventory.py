from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.inventory import InventoryItem
from app.models.scan import FoodScan
from app.models.user import User
from app.schemas.inventory import InventoryItemCreate, InventoryItemOut, InventoryItemUpdate

router = APIRouter(prefix="/inventory", tags=["inventory"])


def _status(expiry_date: date | None) -> tuple[int | None, str]:
    if expiry_date is None:
        return None, "unknown"
    remaining = (expiry_date - date.today()).days
    if remaining < 0:
        return remaining, "expired"
    if remaining <= 3:
        return remaining, "urgent"
    if remaining <= 7:
        return remaining, "soon"
    return remaining, "stored"


def _out(item: InventoryItem) -> InventoryItemOut:
    days_remaining, item_status = _status(item.expiry_date)
    return InventoryItemOut(
        id=item.id,
        product_name=item.product_name,
        category=item.category,
        quantity=item.quantity,
        expiry_date=item.expiry_date,
        expiry_source=item.expiry_source,
        days_remaining=days_remaining,
        status=item_status,
        source_scan_id=item.source_scan_id,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.get("", response_model=list[InventoryItemOut])
def list_inventory(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    rows = (
        db.query(InventoryItem)
        .filter(InventoryItem.user_id == current.id)
        .order_by(InventoryItem.expiry_date.is_(None), InventoryItem.expiry_date.asc(), InventoryItem.created_at.desc())
        .all()
    )
    return [_out(item) for item in rows]


@router.post("", response_model=InventoryItemOut, status_code=status.HTTP_201_CREATED)
def create_inventory_item(
    payload: InventoryItemCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    if payload.source_scan_id and not db.query(FoodScan.id).filter(
        FoodScan.id == payload.source_scan_id, FoodScan.user_id == current.id
    ).first():
        raise HTTPException(status_code=404, detail="Source scan not found")
    name = payload.product_name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Product name is required")
    item = InventoryItem(
        user_id=current.id,
        source_scan_id=payload.source_scan_id,
        product_name=name,
        category=payload.category.strip() if payload.category and payload.category.strip() else None,
        quantity=payload.quantity,
        expiry_date=payload.expiry_date,
        expiry_source=payload.expiry_source,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _out(item)


@router.patch("/{item_id}", response_model=InventoryItemOut)
def update_inventory_item(
    item_id: str,
    payload: InventoryItemUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id, InventoryItem.user_id == current.id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("expiry_source") is None:
        changes.pop("expiry_source")
    if "product_name" in changes and changes["product_name"] is not None:
        changes["product_name"] = changes["product_name"].strip()
        if not changes["product_name"]:
            raise HTTPException(status_code=422, detail="Product name is required")
    if "category" in changes and changes["category"]:
        changes["category"] = changes["category"].strip() or None
    for key, value in changes.items():
        setattr(item, key, value)
    if item.expiry_date is None and item.expiry_source != "unknown":
        raise HTTPException(status_code=422, detail="Choose unknown when no expiry date is available.")
    if item.expiry_date is not None and item.expiry_source == "unknown":
        item.expiry_source = "user_entered"
    if "expiry_date" in changes and "expiry_source" not in changes:
        item.expiry_source = "user_entered" if changes["expiry_date"] else "unknown"
    elif item.expiry_date is None:
        item.expiry_source = "unknown"
    elif item.expiry_source == "unknown":
        item.expiry_source = "user_entered"
    db.commit()
    db.refresh(item)
    return _out(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inventory_item(
    item_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id, InventoryItem.user_id == current.id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    db.delete(item)
    db.commit()
    return None
