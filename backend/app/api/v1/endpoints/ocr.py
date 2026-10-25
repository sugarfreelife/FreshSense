import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.deps import get_current_user
from app.models.user import User
from app.ocr.service import extract_text_from_image
from app.utils.files import MAX_FILE_SIZE_BYTES, validate_size
from app.utils.images import normalize_uploaded_image

router = APIRouter(prefix="/ocr", tags=["ocr"])


class OCRExtractOut(BaseModel):
    raw_text: str
    expiry_date: str | None = None
    date_detected: bool
    provider: str = "unavailable"


class OCRTextIn(BaseModel):
    text: str = Field(max_length=20_000)


@router.post("/extract", response_model=OCRExtractOut)
async def ocr_extract(file: UploadFile, current: User = Depends(get_current_user)):
    contents = await file.read(MAX_FILE_SIZE_BYTES + 1)
    if not validate_size(len(contents)):
        raise HTTPException(status_code=400, detail="File too large. Max 10MB.")
    tmp_dir = os.path.join(settings.UPLOAD_DIR, "tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_path = os.path.join(tmp_dir, f"{uuid.uuid4().hex}.jpg")
    try:
        try:
            normalize_uploaded_image(contents, tmp_path)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return extract_text_from_image(tmp_path)
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


@router.post("/parse-text", response_model=OCRExtractOut)
def ocr_parse_text(payload: OCRTextIn, current: User = Depends(get_current_user)):
    return extract_text_from_image("manual-entry", raw_text_override=payload.text)
