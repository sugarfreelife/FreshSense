# A Multimodal Edge-AI Framework for Food Freshness Assessment and Shelf-Life Prediction Using Vision, VOC Sensing and OCR

**Product name:** FreshSense AI · a student prototype for traceable food-package assessment and batch-level expiry tracking.

Food identity recognition uses a local pretrained CLIP model. See
[backend/PRODUCT_RECOGNITION.md](backend/PRODUCT_RECOGNITION.md) for setup and
limitations. Package details and dates depend on readable label text.

Combines image-based freshness estimates, VOC/environmental sensing (API + ESP32 abstraction), OCR expiry extraction, and deterministic decision rules. A Freshness Passport records the evidence behind each scan; users can link repeat scans to the same named food item and inspect a chronological record of assessments and storage context.

> The “60%” figure in the original Phase-1 plan was an implementation milestone, not measured accuracy or a live readiness score. Assessment is informational, not certified food-safety judgment. Prototype vision output is labeled `prototype`; unfinished fusion and shelf-life features remain research work.

## Stack
- Frontend: React + Vite + TS + Tailwind + PWA (vite-plugin-pwa), React Router, TanStack Query, axios, zod
- Backend: FastAPI + Pydantic v2 + SQLAlchemy + Alembic, PostgreSQL via `DATABASE_URL`, PyJWT/passlib, Uvicorn
- PWA: manifest + service worker (autoUpdate), offline shell, installable, camera capture

## Quick start
```bash
# Windows PowerShell, from the repository root (Python 3.12 and Node.js 20.19+):
py -3.12 -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
npm --prefix frontend install
# On first setup only, copy backend/.env.example to backend/.env and keep its demo SQLite settings.

# Install the Tesseract OCR executable separately. On Windows the app checks
# C:\Program Files\Tesseract-OCR\tesseract.exe as well as PATH.

# Start both services from the repository root:
node start-dev.mjs

# It starts both services, selects available local ports, prints the URLs, and stops with Ctrl+C.
# For phone testing, connect the phone and PC to one Wi-Fi network, then run:
node start-dev.mjs --phone

# Linux/macOS: install the same Python and Node dependencies, plus tesseract-ocr,
# then run node start-dev.mjs from the repository root.
```

For a local demo, the checked-in example uses `sqlite:///./freshsense-demo.db`. On first API start, the app creates its local schema, seeds two repeatable demo accounts, and adds synthetic sample pantry batches to the primary demo account. Both accounts use password `FreshSenseDemo2026!`:

| Email | Name |
|---|---|
| `demo@example.com` | FreshSense Demo |
| `reviewer@example.com` | FreshSense Reviewer |

These shared credentials are for local demos only. The ignored `backend/.env` file can keep this SQLite URL without changing any hosted database. To use PostgreSQL instead, set `DATABASE_URL`, set a random `JWT_SECRET` of at least 32 characters, create the database, and run `alembic upgrade head` before starting the API. Tests use isolated in-memory SQLite by default; set `TEST_DATABASE_URL` to a separate PostgreSQL database ending in `_test` to verify against PostgreSQL. API tests reset their test database tables.

If the application database already has the exact initial schema created by an older app startup, run `alembic stamp head` once instead of `alembic upgrade head`. For any other existing schema, back it up and reconcile it before applying migrations.

## Flow
PWA → register/login → choose Personal or Seller view → scan (camera/upload + optional context) → vision/OCR/decision → Freshness Passport → confirm or enter the package date → record the purchased/received quantity as a separate batch → follow the date watch and scan history.

Uploads accept common raster formats (JPEG, PNG, WebP, GIF, BMP, TIFF, AVIF, and HEIC/HEIF). The original upload is retained privately; an oriented JPEG derivative (up to 2,560 pixels per side) is used for consistent display and faster analysis. Images must be at most 10 MB and 40 megapixels. Clear labels use a fast first OCR pass; difficult labels retain the multi-view retry path.

The inventory keeps each purchase or received-stock batch separate, so the same product can have a different quantity and label date for every lot. Personal view uses pantry/purchase language and private household batches. Seller view uses shared business workspaces: owners can create workspaces, add registered FreshSense accounts as managers or staff, and track batch counts and branch/stock locations. Membership is checked by the API for every business inventory and scan request; an unlisted account cannot access the workspace. The mode and active workspace are saved in this browser. A manager can add staff; only owners can add managers or remove other members. Workspace members can update batches; only owners and managers can delete batches or shared scans. Staff accounts must be registered before an owner can add them.

Seller workspaces provide basic shared stock tracking, but not email invitation/acceptance, ownership transfer, supplier records, point-of-sale integration, or consolidated multi-branch reporting. The Adaptive Review Queue ranks batches using date urgency, date evidence source, and quantity share, and links each recommendation to the batch record. Its priority score is a transparent organizing heuristic, not a model confidence or safety probability, and has not been validated. If OCR does not produce a date, intake asks the user to read and enter the package date or explicitly save the batch without one. Each batch can also record a stock location, storage context, opened date, notes, and an optional reminder window. Browser alerts are checked while the app is open; date-watch figures are organizing cues based on recorded package dates, not food-safety verdicts. See [`DEMO_GUIDE.md`](DEMO_GUIDE.md) for the presentation flow, phone smoke-check, and package-label evaluation.

Scans are paginated (20 per request by default). Uploaded photos are returned through an authenticated, non-cacheable endpoint rather than public static hosting. Apply the new Alembic migration before starting an existing database.

Browser sign-in uses an HttpOnly, SameSite session cookie; production cookies require HTTPS and browser write requests include a CSRF token. The frontend does not persist access tokens in local storage. Logout revokes the presented access token in the database; the OAuth bearer-token endpoint remains available for API clients.

## Production deployment (self-hosted)

The repository includes a Docker Compose deployment with PostgreSQL, persistent upload storage, Alembic migration on API startup, Tesseract OCR, and an Nginx-served PWA with same-origin API routing and browser security headers. Put a trusted TLS reverse proxy in front of port 8080 before making the service public.

1. Install Docker Engine and the Docker Compose plugin on a server.
2. Copy `production.env.example` to `.env.production`. Set `POSTGRES_PASSWORD` to a 64-character random hexadecimal value, `JWT_SECRET` to a separate random value of at least 32 characters, `CORS_ORIGINS` to the app's HTTPS origin, and `WEB_PORT` to the private port your TLS proxy will reach.
3. Start the stack with `docker compose --env-file .env.production up --build -d`.
4. Check `https://your-domain.example/api/v1/health` and complete the release checks in `PRODUCTION.md`.

This supports a single self-hosted application instance. Back up both named volumes (`freshsense-postgres` and `freshsense-uploads`). Multiple API replicas need shared object storage for package photos and operational monitoring before deployment. See [`PRODUCTION.md`](PRODUCTION.md) for the remaining release requirements and limitations.

## AI status
| Component | Status |
|---|---|
| Vision | Interpretable image features; uses a reviewed, locally trained logistic model when `models/vision_model.json` exists, otherwise discloses the prototype fallback |
| Package OCR | Tesseract reads printed labels; a local RapidOCR retry straightens difficult stamps and connects dot-matrix print; the date parser accepts labeled formats, rejects implausible years, and asks for review when evidence is incomplete |
| Fusion/decision | deterministic Phase-1 engine, missing-modality safe |
| Shelf-life regression | Phase 2 (`STATUS: MODEL TRAINING REQUIRED`) |
| Hardware/ESP32 | API + abstraction ready, calibration Phase 2 |

See `ARCHITECTURE.md`, `API.md`, `DEVELOPMENT.md`, `PHASES.md`, `PROJECT_STATUS.md`.
See [backend/AI_MODEL.md](backend/AI_MODEL.md) for the local training workflow and its data requirements.
See [data/README.md](data/README.md) for paired-data collection, leakage-safe splits, and image-versus-Passport evaluation. The repository currently has no labeled dataset, so no training or comparative performance claim is available yet.
See [NOVELTY.md](NOVELTY.md) for the proposed contribution and evaluation criteria.
