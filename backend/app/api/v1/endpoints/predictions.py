import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel

from app.core.config import settings
from app.core.deps import get_current_user
from app.ml.vision.inference import heuristic_predict
from app.models.user import User
from app.utils.files import validate_extension, validate_mime, validate_size
from app.utils.images import verify_image

router = APIRouter(prefix="/predictions", tags=["predictions"])


class VisionResult(BaseModel):
    food_type: str
    freshness: str
    confidence: float
    model_version: str
    model_type: str


@router.post("/vision", response_model=VisionResult)
async def predict_vision(file: UploadFile, current: User = Depends(get_current_user)):
    filename = file.filename or "upload.jpg"
    if not validate_extension(filename):
        raise HTTPException(status_code=400, detail="Unsupported file extension.")
    if not validate_mime(file.content_type):
        raise HTTPException(status_code=400, detail=f"Unsupported MIME type: {file.content_type}")
    contents = await file.read()
    if not validate_size(len(contents)):
        raise HTTPException(status_code=400, detail="File too large. Max 10MB.")
    tmp_dir = os.path.join(settings.UPLOAD_DIR, "tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    ext = os.path.splitext(filename.lower())[1] or ".jpg"
    tmp_path = os.path.join(tmp_dir, f"{uuid.uuid4().hex}{ext}")
    with open(tmp_path, "wb") as f:
        f.write(contents)
    if not verify_image(tmp_path):
        os.remove(tmp_path)
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.")
    try:
        return heuristic_predict(tmp_path)
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
