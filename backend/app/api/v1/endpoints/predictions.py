import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel

from app.core.config import settings
from app.core.deps import get_current_user
from app.ml.vision.inference import predict_image
from app.models.user import User
from app.schemas.scan import ProductRecognitionOut
from app.utils.files import MAX_FILE_SIZE_BYTES, validate_size
from app.utils.images import normalize_uploaded_image

router = APIRouter(prefix="/predictions", tags=["predictions"])


class VisionResult(BaseModel):
    food_type: str
    freshness: str
    confidence: float
    model_version: str
    model_type: str
    confidence_kind: str
    visual_evidence: dict[str, float]
    validation_accuracy: float | None = None
    product_recognition: ProductRecognitionOut | None = None


@router.post("/vision", response_model=VisionResult)
async def predict_vision(file: UploadFile, current: User = Depends(get_current_user)):
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
        return predict_image(tmp_path)
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
