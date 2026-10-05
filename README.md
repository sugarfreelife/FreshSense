# A Multimodal Edge-AI Framework for Food Freshness Assessment and Shelf-Life Prediction Using Vision, VOC Sensing and OCR

**Product name:** FreshSense AI · Phase-1 60% milestone (functional foundation, honest prototype labels).

Combines image-based freshness estimates, VOC/environmental sensing (API + ESP32 abstraction), and OCR expiry extraction + deterministic fusion/decision layer. Scan results include a Freshness Passport that shows which evidence contributed, what was missing, and how the recommendation was produced.

> Assessment is informational, not certified food-safety judgment. Prototype vision output is labeled `prototype`, unfinished fusion/shelf-life as `not_implemented`/Phase 2.

## Stack
- Frontend: React + Vite + TS + Tailwind + PWA (vite-plugin-pwa), React Router, TanStack Query, axios, zod
- Backend: FastAPI + Pydantic v2 + SQLAlchemy + Alembic, PostgreSQL via `DATABASE_URL`, JWT (jose/passlib), Uvicorn
- PWA: manifest + service worker (autoUpdate), offline shell, installable, camera capture

## Quick start
```bash
# backend
cd backend; cp .env.example .env  # configure DATABASE_URL for PostgreSQL
pip install -r requirements.txt
alembic upgrade head  # apply the schema to DATABASE_URL
python -m pytest tests -q
uvicorn app.main:app --reload --port 8000  # docs at /docs, health at /api/v1/health

# frontend
cd frontend; cp .env.example .env  # VITE_API_URL=http://localhost:8000/api/v1
npm install; npm run build; npm run dev  # http://localhost:5173
```

Configure `DATABASE_URL` and `TEST_DATABASE_URL` in `backend/.env` for separate PostgreSQL databases, and set a random `JWT_SECRET` of at least 32 characters. Create both databases first. Run `alembic upgrade head` against the application database before starting the API. Backend API tests reset all project tables in `TEST_DATABASE_URL`; the test runner refuses URLs that do not end in `_test`.

If the application database already has the exact initial schema created by an older app startup, run `alembic stamp head` once instead of `alembic upgrade head`. For any other existing schema, back it up and reconcile it before applying migrations.

## Flow
PWA → register/login → dashboard → scan (camera/upload + optional sensor values) → vision/OCR/fusion/decision → result report → history.

## AI status
| Component | Status |
|---|---|
| Vision | Interpretable image features; uses a reviewed, locally trained logistic model when `models/vision_model.json` exists, otherwise discloses the prototype fallback |
| OCR date parser | real regex; OCR engine optional (EasyOCR/Paddle = Phase 2), never fabricates dates |
| Fusion/decision | deterministic Phase-1 engine, missing-modality safe |
| Shelf-life regression | Phase 2 (`STATUS: MODEL TRAINING REQUIRED`) |
| Hardware/ESP32 | API + abstraction ready, calibration Phase 2 |

See `ARCHITECTURE.md`, `API.md`, `DEVELOPMENT.md`, `PHASES.md`, `PROJECT_STATUS.md`.
See [backend/AI_MODEL.md](backend/AI_MODEL.md) for the local training workflow and its data requirements.
