import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class InventoryItem(Base):
    """A purchased batch of one food product with its own quantity and date."""

    __tablename__ = "inventory_items"
    __table_args__ = (CheckConstraint("quantity > 0", name="ck_inventory_quantity_positive"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_scan_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("food_scans.id", ondelete="SET NULL"), nullable=True, index=True
    )
    product_name: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_source: Mapped[str] = mapped_column(String(24), nullable=False, default="unknown")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    source_scan = relationship("FoodScan", lazy="joined")
