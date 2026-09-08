# ARCHITECTURE

```
PWA (React+Vite) → FastAPI (/api/v1: auth/scan/vision/ocr/sensor/assessment/health)
 → services (expiry, fusion, decision, assessment) → ml/vision (prototype) | ocr (parser+provider) | sensors (provider)
 → fusion evidence {vision, sensor, ocr} → decision (freshness/confidence/recommendation/warnings/modalities_used)
 → SQLAlchemy models (User, FoodScan, VisionPrediction, OCRResult, SensorReading, FinalAssessment, ModelVersion) → PostgreSQL/SQLite
```
Layered: routes → services → ml/ocr/sensors; no model logic in routes; no frontend→DB coupling; env-based secrets.
Future: swap vision-v0.1-prototype for trained MobileNetV3 via `ml/base.py ModelInterface`; learned fusion plugs into `ml/fusion/model.py` consuming `visual_features/sensor_features/ocr_features`.
