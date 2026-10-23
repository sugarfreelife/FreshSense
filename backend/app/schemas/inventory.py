from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


ExpirySource = Literal["ocr_confirmed", "user_entered", "unknown"]
StorageLocation = Literal["unknown", "pantry", "refrigerator", "freezer", "room_temperature", "other"]


class InventoryItemCreate(BaseModel):
    product_name: str = Field(min_length=1, max_length=160)
    category: str | None = Field(default=None, max_length=80)
    quantity: int = Field(default=1, ge=1, le=9999)
    expiry_date: date | None = None
    expiry_source: ExpirySource = "unknown"
    reminder_days_before: Literal[1, 3, 7] | None = None
    storage_location: StorageLocation = "unknown"
    opened_date: date | None = None
    storage_notes: str | None = Field(default=None, max_length=500)
    source_scan_id: str | None = Field(default=None, max_length=36)

    @model_validator(mode="after")
    def expiry_source_matches_date(self):
        if self.expiry_date is None and self.expiry_source != "unknown":
            raise ValueError("Choose unknown when no expiry date is available.")
        if self.expiry_date is not None and self.expiry_source == "unknown":
            raise ValueError("Choose whether the date was read or entered by the user.")
        if self.expiry_date is None and self.reminder_days_before is not None:
            raise ValueError("Add a package date before setting a reminder.")
        return self


class InventoryItemUpdate(BaseModel):
    product_name: str | None = Field(default=None, min_length=1, max_length=160)
    category: str | None = Field(default=None, max_length=80)
    quantity: int | None = Field(default=None, ge=1, le=9999)
    expiry_date: date | None = None
    expiry_source: ExpirySource | None = None
    reminder_days_before: Literal[1, 3, 7] | None = None
    storage_location: StorageLocation = "unknown"
    opened_date: date | None = None
    storage_notes: str | None = Field(default=None, max_length=500)


class InventoryItemOut(BaseModel):
    id: str
    product_name: str
    category: str | None = None
    quantity: int
    expiry_date: date | None = None
    expiry_source: ExpirySource
    reminder_days_before: int | None = None
    storage_location: StorageLocation = "unknown"
    opened_date: date | None = None
    storage_notes: str | None = None
    days_remaining: int | None = None
    status: Literal["expired", "urgent", "soon", "stored", "unknown"]
    source_scan_id: str | None = None
    created_at: datetime
    updated_at: datetime
