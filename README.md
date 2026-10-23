# A Multimodal Edge-AI Framework for Food Freshness Assessment and Shelf-Life Prediction Using Vision, VOC Sensing and OCR

**Product name:** FreshSense AI · Phase-1 60% milestone (functional foundation, honest prototype labels).

Combines image-based freshness estimates, VOC/environmental sensing (API + ESP32 abstraction), OCR expiry extraction, and deterministic decision rules. A Freshness Passport records the evidence behind each scan; users can link repeat scans to the same named food item and inspect a chronological record of assessments and storage context.

> Assessment is informational, not certified food-safety judgment. Prototype vision output is labeled `prototype`, unfinished fusion/shelf-life as `not_implemented`/Phase 2.

## Stack
- Frontend: React + Vite + TS + Tailwind + PWA (vite-plugin-pwa), React Router, TanStack Query, axios, zod
- Backend: FastAPI + Pydantic v2 + SQLAlchemy + Alembic, PostgreSQL via `DATABASE_URL`, JWT (jose/passlib), Uvicorn
- PWA: manifest + service worker (autoUpdate), offline shell, installable, camera capture

## Quick start
```bash
# macOS/Linux (requires Node.js/npm and the project dependencies below)
./start-dev.sh

# Windows Command Prompt (same prerequisites)
start-dev.cmd

# Or on any platform
node start-dev.mjs

# The launchers start both services; stop them with Ctrl+C.

# backend
cd backend; cp .env.example .env  # local demo uses SQLite; PostgreSQL is optional
pip install -r requirements.txt
alembic upgrade head  # apply the schema to DATABASE_URL when using PostgreSQL
python -m pytest tests -q
uvicorn app.main:app --reload --port 8000  # docs at /docs, health at /api/v1/health

# frontend
cd frontend; cp .env.example .env  # VITE_API_URL=http://localhost:8000/api/v1
npm install; npm run build; npm run dev  # http://localhost:5173
```

For a local demo, the checked-in example uses `sqlite:///./freshsense-demo.db`. On first API start, the app creates its local schema and seeds two repeatable demo accounts. Both use password `FreshSenseDemo2026!`:

| Email | Name |
|---|---|
| `demo@example.com` | FreshSense Demo |
| `reviewer@example.com` | FreshSense Reviewer |

These shared credentials are for local demos only. The ignored `backend/.env` file can keep this SQLite URL without changing any hosted database. To use PostgreSQL instead, set `DATABASE_URL`, set a random `JWT_SECRET` of at least 32 characters, create the database, and run `alembic upgrade head` before starting the API. Keep `TEST_DATABASE_URL` pointed at a separate PostgreSQL database ending in `_test`; API tests reset its project tables.

If the application database already has the exact initial schema created by an older app startup, run `alembic stamp head` once instead of `alembic upgrade head`. For any other existing schema, back it up and reconcile it before applying migrations.

## Flow
PWA → register/login → scan (camera/upload + optional context) → vision/OCR/decision → Freshness Passport → confirm or enter the package date → record the purchased quantity as a pantry batch → follow the date watch and scan history.

The Pantry keeps each purchase batch separate, so the same product can have a different quantity and label date on each purchase. If OCR does not produce a date, stock intake asks the user to read and enter the package date or explicitly save the batch without one. Each batch can also record storage location, opened date, notes, and an optional reminder window. Browser alerts are checked while the app is open; the pantry's “use next” cue sorts recorded dates and explains its recommendation. These are organizing aids, not food-safety verdicts. Inventory is private to the signed-in user. See [`DEMO_GUIDE.md`](DEMO_GUIDE.md) for the presentation flow, phone smoke-check, and package-label evaluation.

Scans are paginated (20 per request by default). Uploaded photos are returned through an authenticated, non-cacheable endpoint rather than public static hosting. Apply the new Alembic migration before starting an existing database.

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
See [data/README.md](data/README.md) for paired-data collection, leakage-safe splits, and image-versus-Passport evaluation. The repository currently has no labeled dataset, so no training or comparative performance claim is available yet.
See [NOVELTY.md](NOVELTY.md) for the proposed contribution and evaluation criteria.
