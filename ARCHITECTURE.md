# ARCHITECTURE

```
PWA (React+Vite) → FastAPI (/api/v1: auth/scan/tracked-items/vision/ocr/sensor/assessment/health)
 → services (expiry, fusion, decision, assessment) → ml/vision (prototype) | ocr (parser+provider) | sensors (provider)
 → per-scan evidence and decision → Freshness Passport → optional TrackedItem timeline grouping repeat scans
 → SQLAlchemy models (User, TrackedItem, FoodScan, VisionPrediction, OCRResult, SensorReading, FinalAssessment, ModelVersion) → PostgreSQL
```
Layered: routes → services → ml/ocr/sensors; no model logic in routes; no frontend→DB coupling; env-based secrets.
Future: swap vision-v0.1-prototype for trained MobileNetV3 via `ml/base.py ModelInterface`; learned fusion plugs into `ml/fusion/model.py` consuming `visual_features/sensor_features/ocr_features`.

Scan history uses bounded offset pagination. Uploaded images are served from an authenticated endpoint scoped to the owning user and are marked private/no-store; API paths are excluded from the PWA runtime cache. A longitudinal item response returns that user's scans in chronological order.
