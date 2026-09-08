from fastapi import APIRouter

from app.api.v1.endpoints import assessments, auth, health, ocr, predictions, scans, sensors

router = APIRouter()
router.include_router(health.router)
router.include_router(auth.router)
router.include_router(scans.router)
router.include_router(predictions.router)
router.include_router(ocr.router)
router.include_router(sensors.router)
router.include_router(assessments.router)
