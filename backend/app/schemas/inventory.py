from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


ExpirySource = Literal["ocr_confirmed", "user_entered", "unknown"]


class InventoryItemCreate(BaseModel):
    product_name: str = Field(min_length=1, max_length=160)
    category: str | None = Field(default=None, max_length=80)
    quantity: int = Field(default=1, ge=1, le=9999)
    expiry_date: date | None = None
    expiry_source: ExpirySource = "unknown"
    source_scan_id: str | None = Field(default=None, max_length=36)

    @model_validator(mode="after")
    def expiry_source_matches_date(self):
        if self.expiry_date is None and self.expiry_source != "unknown":
            raise ValueError("Choose unknown when no expiry date is available.")
        if self.expiry_date is not None and self.expiry_source == "unknown":
            raise ValueError("Choose whether the date was read or entered by the user.")
        return self


class InventoryItemUpdate(BaseModel):
    product_name: str | None = Field(default=None, min_length=1, max_length=160)
    category: str | None = Field(default=None, max_length=80)
    quantity: int | None = Field(default=None, ge=1, le=9999)
    expiry_date: date | None = None
    expiry_source: ExpirySource | None = None


class InventoryItemOut(BaseModel):
    id: str
    product_name: str
    category: str | None = None
    quantity: int
    expiry_date: date | None = None
    expiry_source: ExpirySource
    days_remaining: int | None = None
    status: Literal["expired", "urgent", "soon", "stored", "unknown"]
    source_scan_id: str | None = None
    created_at: datetime
    updated_at: datetime
