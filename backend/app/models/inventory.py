import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.utils.time import utcnow_naive


def _uuid() -> str:
    return str(uuid.uuid4())


class InventoryItem(Base):
    """A purchased batch of one food product with its own quantity and date."""

    __tablename__ = "inventory_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_inventory_quantity_positive"),
        CheckConstraint(
            "reminder_days_before IS NULL OR reminder_days_before IN (1, 3, 7)",
            name="ck_inventory_reminder_days",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("business_workspaces.id", ondelete="CASCADE"), nullable=True, index=True
    )
    source_scan_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("food_scans.id", ondelete="SET NULL"), nullable=True, index=True
    )
    product_name: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_source: Mapped[str] = mapped_column(String(24), nullable=False, default="unknown")
    reminder_days_before: Mapped[int | None] = mapped_column(Integer, nullable=True)
    storage_location: Mapped[str] = mapped_column(String(40), nullable=False, default="unknown")
    stock_location: Mapped[str | None] = mapped_column(String(120), nullable=True)
    opened_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    storage_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow_naive, onupdate=utcnow_naive)

    source_scan = relationship("FoodScan", lazy="joined")
    workspace = relationship("BusinessWorkspace", back_populates="inventory_items")
