# A Multimodal Edge-AI Framework for Food Freshness Assessment and Shelf-Life Prediction Using Vision, VOC Sensing and OCR

**Product name:** FreshSense AI · Phase-1 60% milestone (functional foundation, honest prototype labels).

Combines vision (prototype MobileNetV3-ready interface), VOC/environmental sensing (API + ESP32 abstraction), and OCR expiry extraction + deterministic fusion/decision layer.

> Assessment is informational, not certified food-safety judgment. Prototype vision output is labeled `prototype`, unfinished fusion/shelf-life as `not_implemented`/Phase 2.

## Stack
- Frontend: React + Vite + TS + Tailwind + PWA (vite-plugin-pwa), React Router, TanStack Query, axios, zod
- Backend: FastAPI + Pydantic v2 + SQLAlchemy + Alembic, JWT (jose/passlib), SQLite dev fallback / PostgreSQL via `DATABASE_URL`, Uvicorn
- PWA: manifest + service worker (autoUpdate), offline shell, installable, camera capture

## Quick start
```bash
# backend
cd backend; cp .env.example .env  # or leave unset for SQLite fallback
pip install -r requirements.txt
python -m pytest tests -q
uvicorn app.main:app --reload --port 8000  # docs at /docs, health at /api/v1/health

# frontend
cd frontend; cp .env.example .env  # VITE_API_URL=http://localhost:8000/api/v1
npm install; npm run build; npm run dev  # http://localhost:5173
```
Docker: `docker-compose up --build` (postgres + backend + frontend).

## Flow
PWA → register/login → dashboard → scan (camera/upload + optional sensor values) → vision/OCR/fusion/decision → result report → history.

## AI status
| Component | Status |
|---|---|
| Vision | `prototype` heuristic (vision-v0.1-prototype), MobileNetV3 training = Phase 2 |
| OCR date parser | real regex; OCR engine optional (EasyOCR/Paddle = Phase 2), never fabricates dates |
| Fusion/decision | deterministic Phase-1 engine, missing-modality safe |
| Shelf-life regression | Phase 2 (`STATUS: MODEL TRAINING REQUIRED`) |
| Hardware/ESP32 | API + abstraction ready, calibration Phase 2 |

See `ARCHITECTURE.md`, `API.md`, `DEVELOPMENT.md`, `PHASES.md`, `PROJECT_STATUS.md`.
