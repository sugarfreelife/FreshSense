# AI-Based Multimodal Food Freshness and Expiry Detection System
## Agent Build Specification — Phase 1 (60% Completion Target)

> **Role:** You are the primary senior full-stack + AI/ML engineer responsible for starting the implementation of this academic project.
>
> **Primary objective:** Build approximately **60% of the complete project as a genuinely functional, extensible foundation**. Do not create fake/demo-only functionality just to claim completion. Every implemented feature must work end-to-end where its required dependency is available, and unfinished research/hardware components must be clearly isolated behind clean interfaces.

---

# 1. Project Context

The project is an academic/research-oriented system for **multimodal food freshness and expiry assessment**.

The literature review identifies a gap in existing systems: most approaches use a single modality (vision, gas/VOC, or OCR), while the proposed work combines:

1. **Computer vision** for food appearance/freshness assessment.
2. **Gas/VOC + environmental sensing** for chemical/environmental spoilage signals.
3. **OCR** for extracting printed expiry/best-before dates.
4. **A multimodal fusion/decision layer** to combine evidence.
5. **Shelf-life estimation** where sufficient data supports it.
6. **Lightweight/edge-oriented deployment**.
7. **A user-facing application with actionable results and history**.

The literature review specifically proposes a visual branch, chemical/sensor branch, OCR branch, fusion/decision layer, and application layer. It also emphasizes robustness when one modality is missing or degraded.

Reference: the supplied literature review, especially the sections on innovation and proposed architecture.

---

# 2. Working Project Title

Use this working title throughout the code/documentation unless the project owner changes it:

**A Multimodal Edge-AI Framework for Food Freshness Assessment and Shelf-Life Prediction Using Vision, VOC Sensing and OCR**

A shorter UI/product name may be:

**FreshSense AI**

Do not change the academic title without explicit approval.

---

# 3. Critical Instruction: Build 60%, Not 100%

The first implementation milestone is **60% of the complete project**.

The 60% milestone must establish a strong, runnable foundation containing:

- production-quality project structure
- React + Vite frontend
- **PWA support**
- responsive/mobile-first UI
- FastAPI backend
- database layer
- authentication foundation
- image upload/capture flow
- OCR pipeline
- initial food/freshness AI inference pipeline
- prediction/report API
- scan history
- sensor-data API and data model
- multimodal architecture interfaces
- model/evaluation scaffolding
- Local development setup
- documentation
- tests for important backend/frontend functionality

The following can remain as clearly marked Phase 2 work:

- fully trained multimodal fusion model
- extensive controlled food-aging dataset
- final hardware integration
- extensive sensor calibration
- rigorous shelf-life regression model
- advanced edge quantization/deployment
- complete production deployment
- large-scale benchmarking
- advanced admin/research analytics

**Do not fake these unfinished components.**

Instead, create clean interfaces, mock/sample adapters where necessary, and TODO/Phase-2 documentation explaining exactly where the real implementation will plug in.

---

# 4. Non-Negotiable Engineering Principles

Follow these principles throughout implementation:

### 4.1 No monolithic code

Separate:

- UI
- API
- ML inference
- data processing
- database
- sensor integration
- OCR
- configuration

### 4.2 No hard-coded secrets

Use environment variables and `.env.example`.

Never commit:

- API keys
- passwords
- tokens
- private credentials

### 4.3 No fake AI claims

If a model is not trained yet, do not label a deterministic demo rule as an AI prediction.

Clearly distinguish:

- `real_model`
- `prototype/mock`
- `not_implemented`

### 4.4 Build for extension

The final multimodal fusion model must be able to consume:

```text
visual_features
sensor_features
ocr_features
```

without requiring a rewrite of the backend.

### 4.5 Mobile-first

The intended usage includes taking a food photo using a phone.

Therefore the application must work extremely well on mobile screen sizes.

---

# 5. Target Architecture

Implement the following architecture:

```text
                         ┌──────────────────────┐
                         │      USER DEVICE     │
                         │                      │
                         │ React + Vite PWA     │
                         │ Camera / Upload       │
                         └──────────┬───────────┘
                                    │
                               HTTPS / REST
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │       FastAPI        │
                         │       Backend        │
                         ├──────────────────────┤
                         │ Auth                 │
                         │ Scan API             │
                         │ OCR API              │
                         │ Prediction API       │
                         │ Sensor API           │
                         │ History API          │
                         └──────────┬───────────┘
                                    │
             ┌──────────────────────┼──────────────────────┐
             │                      │                      │
             ▼                      ▼                      ▼
      ┌────────────┐         ┌────────────┐        ┌────────────┐
      │ Vision     │         │ OCR        │        │ Sensor     │
      │ Model      │         │ Pipeline   │        │ Pipeline   │
      └─────┬──────┘         └─────┬──────┘        └─────┬──────┘
            │                      │                      │
            └──────────────────────┼──────────────────────┘
                                   ▼
                         ┌──────────────────────┐
                         │ Feature / Evidence   │
                         │ Normalization Layer  │
                         └──────────┬───────────┘
                                    ▼
                         ┌──────────────────────┐
                         │ Multimodal Fusion    │
                         │ Interface            │
                         └──────────┬───────────┘
                                    ▼
                         ┌──────────────────────┐
                         │ Decision Engine      │
                         ├──────────────────────┤
                         │ Freshness            │
                         │ Confidence           │
                         │ Expiry               │
                         │ Recommendation       │
                         │ Shelf-life*          │
                         └──────────┬───────────┘
                                    ▼
                         ┌──────────────────────┐
                         │ PostgreSQL           │
                         │ Scan History         │
                         │ Predictions          │
                         │ Sensor Data          │
                         │ OCR Results          │
                         └──────────────────────┘

* Shelf-life regression is a Phase-2 research component unless a validated
  model/dataset becomes available during Phase 1.
```

---

# 6. Technology Stack

Use this stack unless there is a strong technical reason to change it.

## Frontend

- React
- Vite
- TypeScript
- React Router
- Tailwind CSS
- PWA plugin for Vite
- TanStack Query or an equivalent clean API-state solution
- Zod or equivalent runtime validation where useful

## PWA

The React/Vite application MUST be a real installable PWA.

Implement:

- Web App Manifest
- service worker
- offline app shell
- installability
- icons
- splash/theme metadata
- responsive layout
- camera capture support where browser permits
- graceful offline state
- cached static assets
- appropriate update strategy

The PWA must not merely have a manifest file. Verify that the service worker and installation behavior are actually configured.

Do not claim full offline AI inference unless the model is actually available locally.

---

# 7. Backend

Use:

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- PostgreSQL
- JWT-based authentication
- Uvicorn

Use a clean layered architecture such as:

```text
backend/
├── app/
│   ├── main.py
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── repositories/
│   ├── ml/
│   ├── ocr/
│   ├── sensors/
│   └── utils/
├── tests/
├── alembic/
├── requirements.txt
└── .env.example
```

---

# 8. AI/ML Architecture

## Vision model

Primary planned architecture:

**MobileNetV3-family model**

Reason:

- lightweight
- suitable for transfer learning
- compatible with eventual edge deployment
- consistent with the literature review's lightweight deployment direction

Possible experimentation models:

- MobileNetV3
- ResNet18
- EfficientNet-B0

Do not unnecessarily train huge models.

The initial vision pipeline should expose a stable interface like:

```python
predict_image(image) -> VisionPrediction
```

Example output:

```json
{
  "food_type": "tomato",
  "freshness": "moderately_fresh",
  "confidence": 0.913,
  "model_version": "vision-v0.1"
}
```

---

# 9. Freshness Classes

Initial application-level freshness classes:

```text
fresh
moderately_fresh
spoiled
```

Use a centralized enum/configuration.

Do not scatter strings like `"Fresh"` and `"fresh"` throughout the codebase.

---

# 10. OCR Pipeline

Implement a real OCR service interface.

Preferred OCR options:

- PaddleOCR
- EasyOCR

The pipeline should support:

```text
Image
  ↓
OCR
  ↓
Raw extracted text
  ↓
Date candidate extraction
  ↓
Date normalization
  ↓
Validation
  ↓
Expiry result
```

It should recognize common patterns such as:

```text
EXP 12/09/2026
EXP: 12-09-2026
BEST BEFORE 12/09/2026
BB: 09/2026
```

Handle failure gracefully:

```json
{
  "date_detected": false,
  "raw_text": "...",
  "expiry_date": null,
  "confidence": 0.0,
  "message": "No reliable expiry date detected"
}
```

Do not fabricate an expiry date.

---

# 11. Expiry Logic

Implement date calculations in a dedicated service.

Outputs may include:

```text
expiry_date
days_remaining
expiry_status
```

Example statuses:

```text
valid
expiring_soon
expired
unknown
```

Important:

**Printed expiry information and AI freshness assessment are separate evidence sources.**

Do not automatically treat:

```text
not expired = fresh
```

or:

```text
expired = visually spoiled
```

The system should be capable of reporting disagreement.

Example:

```text
Printed date: VALID
Vision:       SPOILED

→ Warning:
  "The food is within the printed date range, but the visual model
   detected signs associated with spoilage."
```

This is an assessment, not a certified food-safety judgment.

---

# 12. Sensor Architecture

Create a sensor abstraction even before physical hardware is connected.

Interface concept:

```python
class SensorProvider:
    def read(self) -> SensorReading:
        ...
```

Data model:

```text
timestamp
gas_value
temperature
humidity
device_id
```

The backend must support receiving sensor readings through an API.

Example endpoint:

```text
POST /api/v1/sensors/readings
```

Do not assume sensor readings are always available.

---

# 13. Planned Hardware

The intended prototype architecture is:

```text
VOC/Gas Sensor
      +
Temperature Sensor
      +
Humidity Sensor
      ↓
     ESP32
      ↓
 Wi-Fi / Bluetooth
      ↓
 FastAPI backend
```

Potential initial hardware:

- ESP32
- MQ-series gas sensor for prototype experimentation
- DHT22 or BME280

Because MQ sensors can be affected by environmental contaminants and calibration drift, sensor calibration and environmental robustness must be treated as research tasks rather than hidden assumptions.

---

# 14. Multimodal Fusion Interface

For Phase 1, create the complete software interface even if the final trained fusion model is not ready.

Define a normalized evidence structure:

```json
{
  "vision": {
    "food_type": "tomato",
    "freshness": "moderately_fresh",
    "confidence": 0.91,
    "features": []
  },
  "sensor": {
    "gas": 421.2,
    "temperature": 27.1,
    "humidity": 62.4,
    "features": []
  },
  "ocr": {
    "expiry_date": "2026-09-15",
    "days_remaining": 7,
    "confidence": 0.94
  }
}
```

Then create:

```text
FusionService
DecisionService
RecommendationService
```

The architecture must later allow:

```text
Vision only
Vision + Sensor
Vision + OCR
Sensor + OCR
Vision + Sensor + OCR
```

This is essential for the future ablation study.

---

# 15. Conflict-Aware Decision Layer

Implement an initial deterministic decision layer only as a clearly documented **Phase-1 decision engine**, not as the final research model.

Example:

```text
Vision says SPOILED
+
VOC is high
+
Expiry date is still valid

→ HIGH_CONCERN
```

Another:

```text
Vision says FRESH
+
VOC normal
+
Expiry date expired

→ EXPIRY_WARNING
```

Another:

```text
No OCR date
+
Vision available
+
Sensor available

→ Use available modalities
```

The system must never crash because one modality is missing.

---

# 16. Missing-Modality Handling

This is a required architectural feature.

The final application must gracefully handle:

### Case A

```text
Vision + Sensor + OCR
```

### Case B

```text
Vision + Sensor
```

### Case C

```text
Vision + OCR
```

### Case D

```text
Vision only
```

### Case E

```text
OCR only
```

when the user is checking a packaged food label.

Every result should disclose which modalities were actually used.

Example:

```text
Analysis sources:
✓ Camera
✓ VOC sensor
✓ Expiry OCR
```

or:

```text
Analysis sources:
✓ Camera
✗ VOC sensor unavailable
✓ Expiry OCR
```

---

# 17. Database Design

Create PostgreSQL schema using SQLAlchemy + Alembic.

Minimum entities:

## User

```text
id
email
password_hash
role
created_at
```

## FoodScan

```text
id
user_id
image_url/path
food_type
created_at
```

## VisionPrediction

```text
id
scan_id
food_type
freshness
confidence
model_version
created_at
```

## OCRResult

```text
id
scan_id
raw_text
expiry_date
days_remaining
confidence
created_at
```

## SensorReading

```text
id
scan_id/device_id
timestamp
gas_value
temperature
humidity
```

## FinalAssessment

```text
id
scan_id
freshness
confidence
expiry_status
days_remaining
recommendation
modalities_used
model_version
created_at
```

## ModelVersion

```text
id
name
version
type
metrics
created_at
```

Keep room for future:

```text
ShelfLifePrediction
FusionPrediction
ExperimentRun
```

---

# 18. API Specification

Use versioned APIs:

```text
/api/v1/
```

Minimum endpoints:

### Authentication

```text
POST /auth/register
POST /auth/login
GET  /auth/me
```

### Scan

```text
POST /scans
GET  /scans
GET  /scans/{scan_id}
DELETE /scans/{scan_id}
```

### Vision

```text
POST /predictions/vision
```

### OCR

```text
POST /ocr/extract
```

### Sensors

```text
POST /sensors/readings
GET  /sensors/readings
```

### Assessment

```text
POST /assessments
GET  /assessments/{scan_id}
```

### Health

```text
GET /health
```

Generate OpenAPI documentation automatically through FastAPI.

---

# 19. React Application

Build the following screens.

## 19.1 Landing page

Include:

- project/product identity
- short explanation
- CTA: `Start Scan`
- explanation of multimodal assessment
- responsive design

---

## 19.2 Authentication

Pages:

```text
Login
Register
```

Use proper loading/error states.

---

## 19.3 Dashboard

Display:

- total scans
- fresh items
- items needing attention
- recently scanned foods
- quick scan CTA

---

## 19.4 Scan page

This is one of the most important screens.

Features:

- camera capture
- image upload
- preview
- retake/remove
- optional sensor connection status
- scan button
- processing state

Design mobile-first.

---

# 20. Result Page

Create a high-quality report UI.

Example:

```text
------------------------------------
           TOMATO
------------------------------------

Freshness
MODERATELY FRESH

Confidence
91.3%

------------------------------------

Expiry
15 Sep 2026

7 days remaining

------------------------------------

VOC
Normal

Temperature
27.1°C

Humidity
62%

------------------------------------

Recommendation
CONSUME SOON

------------------------------------

Analysis Sources
✓ Vision
✓ VOC Sensor
✓ OCR
```

Also show uncertainty/warnings where applicable.

---

# 21. History Page

Show:

- scan date
- food
- freshness
- confidence
- expiry status

Allow users to open previous reports.

---

# 22. PWA Requirements — NON-NEGOTIABLE

The React/Vite frontend must be developed as a PWA from the beginning.

Implement:

### Manifest

Include:

- name
- short name
- description
- start URL
- display mode
- theme color
- background color
- icons
- appropriate mobile metadata

### Service Worker

Cache:

- application shell
- static assets

Support:

- offline launch
- graceful offline page/state
- cache versioning/update strategy

### Installability

Test:

- Chrome desktop
- Android Chrome if available

### Camera

Use browser camera APIs where supported.

Do not assume camera APIs work identically on every browser.

### Offline behavior

When offline:

```text
App opens
↓
User can view cached UI/history where available
↓
New server-dependent analysis clearly shows:
"Connection required for AI analysis"
```

Do not fake offline predictions.

---

# 23. Frontend UX Requirements

The interface should feel like a real AI product, not a college CRUD project.

Use:

- clear visual hierarchy
- accessible typography
- responsive cards
- loading skeletons
- progress states
- error states
- empty states
- toast/inline notifications
- mobile bottom navigation where appropriate
- accessible buttons
- keyboard navigation
- meaningful icons
- clear confidence display

Do not over-animate.

---

# 24. State Management

Separate:

### Server state

Use TanStack Query or equivalent.

### Local UI state

Use React state/context where appropriate.

Do not create a massive global state store unless necessary.

---

# 25. File Upload Security

Backend must validate:

- file type
- MIME type
- maximum file size
- image decoding
- malformed files

Never trust the extension alone.

Do not execute uploaded files.

---

# 26. Model Service Architecture

Use interfaces so models can be swapped.

Example:

```text
ml/
├── base.py
├── vision/
│   ├── model.py
│   ├── preprocessing.py
│   └── inference.py
├── fusion/
│   ├── model.py
│   └── inference.py
├── shelf_life/
│   └── model.py
└── registry.py
```

The backend should not contain model-specific logic inside route handlers.

---

# 27. Development Dataset

For Phase 1:

- use a documented public dataset if available and licensing permits
- or a small project dataset
- structure data consistently

Suggested structure:

```text
data/
├── raw/
├── processed/
├── train/
├── validation/
├── test/
└── metadata/
```

Metadata should include:

```text
image_id
food_type
freshness_label
capture_date
source
conditions
```

Do not mix training and test images from the same near-duplicate capture session without documenting it.

---

# 28. ML Evaluation Foundation

Create evaluation scripts/notebooks for:

- accuracy
- precision
- recall
- F1-score
- confusion matrix

For future shelf-life regression:

- MAE
- RMSE
- R²

For future edge deployment:

- model size
- inference latency
- memory usage

Do not invent metrics.

If no trained model exists yet, show:

```text
STATUS: MODEL TRAINING REQUIRED
```

instead of fake accuracy.

---

# 29. Explainability Foundation

Prepare the architecture for Grad-CAM or equivalent visual explanation.

The future result should support:

```text
original image
+
attention/activation heatmap
```

For Phase 1, implement the interface/component and integrate it only if the selected model supports it reliably.

---

# 30. Testing

Minimum testing requirements:

## Backend

Use pytest.

Test:

- registration
- login
- authentication
- invalid uploads
- OCR parsing
- date calculations
- missing modality handling
- assessment generation
- sensor input validation

## Frontend

Use appropriate React testing tools.

Test:

- routing
- scan form
- upload state
- result rendering
- error state
- PWA-related application behavior where practical

## Integration

At least one end-to-end path:

```text
Upload image
↓
Backend receives it
↓
Vision/OCR services run
↓
Assessment generated
↓
Result displayed in frontend
↓
Scan stored in database
↓
History displays scan
```

---

# 32. Environment Configuration

Provide:

```text
.env.example
```

Potential variables:

```text
DATABASE_URL=postgresql+psycopg2://freshsense:freshsense@localhost:5432/freshsense
JWT_SECRET=
MODEL_PATH=
UPLOAD_DIR=
OCR_PROVIDER=
CORS_ORIGINS=
```

Never commit `.env`.

---

# 33. Documentation

Create/update:

```text
README.md
ARCHITECTURE.md
API.md
DEVELOPMENT.md
PHASES.md
```

README must explain:

- project purpose
- architecture
- technology stack
- setup
- run instructions
- PWA installation
- API
- AI status
- known limitations
- Phase 2 roadmap

---

# 34. Project Completion Tracking

Create:

```text
PROJECT_STATUS.md
```

with a table like:

| Component | Status | Completion |
|---|---|---:|
| Project architecture | Done | 100% |
| React/Vite | Done | 100% |
| PWA | Done | 100% |
| Backend | Done | 80% |
| Database | Done | 80% |
| Authentication | Done | 80% |
| Image pipeline | Done | 80% |
| OCR | Done | 70% |
| Vision model | Prototype | 60% |
| Sensor API | Foundation | 50% |
| Hardware | Phase 2 | 10% |
| Multimodal fusion | Foundation | 30% |
| Shelf-life prediction | Phase 2 | 10% |
| Explainability | Foundation | 25% |
| Testing | In progress | 60% |
| Documentation | In progress | 70% |

These are planning indicators only. Update them honestly based on what actually exists.

---

# 35. What the Agent Must NOT Do

Do NOT:

- rewrite the entire repository blindly
- delete existing useful work without inspection
- use fake AI predictions
- hard-code prediction results
- hard-code expiry dates
- store secrets in source code
- make the frontend depend directly on database internals
- tightly couple sensor hardware to business logic
- build a fake PWA consisting only of `manifest.json`
- claim offline AI if inference is server-dependent
- claim food-safety certification
- claim a model accuracy that has not been measured
- invent research results
- fabricate datasets
- fabricate literature references
- install dozens of unnecessary dependencies
- introduce a complex microservice architecture prematurely
- build an admin dashboard before the core scan workflow works

---

# 36. Priority Order

Build in this order:

## Priority 1 — Foundation

1. Inspect existing project/repository.
2. Establish architecture.
3. Set up Git-safe environment configuration.
4. Set up React + Vite + TypeScript.
5. Configure PWA.
6. Set up FastAPI.
7. Set up PostgreSQL.
8. Set up SQLAlchemy + Alembic.

## Priority 2 — Core User Workflow

9. Authentication.
10. Dashboard.
11. Scan page.
12. Image upload/camera.
13. Backend image handling.
14. Vision inference interface.
15. OCR pipeline.
16. Expiry calculation.
17. Assessment service.
18. Result page.
19. History.

## Priority 3 — Multimodal Foundation

20. Sensor data models.
21. Sensor API.
22. Sensor service abstraction.
23. Evidence normalization.
24. Fusion service interface.
25. Missing-modality handling.
26. Conflict-aware decision logic.

## Priority 4 — Quality

27. Tests.
28. Error handling.
29. Loading states.
30. Security validation.
31. Local development setup.
32. Documentation.
33. PWA testing.
34. Project status tracking.

---

# 37. Definition of Done for the 60% Milestone

The Phase-1 implementation is considered complete only when a user can perform this flow:

```text
OPEN PWA
   ↓
REGISTER / LOGIN
   ↓
OPEN DASHBOARD
   ↓
START SCAN
   ↓
CAPTURE / UPLOAD FOOD IMAGE
   ↓
PROCESS IMAGE
   ↓
RUN AVAILABLE AI/OCR SERVICES
   ↓
EXTRACT EXPIRY DATE IF PRESENT
   ↓
COMBINE AVAILABLE EVIDENCE
   ↓
GENERATE ASSESSMENT
   ↓
SHOW RESULT
   ↓
SAVE RESULT
   ↓
OPEN HISTORY
   ↓
VIEW PREVIOUS REPORT
```

The application must also:

- run locally
- have working frontend/backend communication
- persist data
- have proper error handling
- be installable as a PWA
- work responsively on mobile
- expose API documentation
- have tests
- have documented limitations
- clearly identify incomplete Phase-2 research components

---

# 38. Phase 2 Roadmap — Do Not Fully Implement Yet

After the 60% milestone, the remaining work should be planned around:

### A. Controlled food-aging dataset

Collect:

```text
Day 0 → Day N
```

for selected foods while recording:

- image
- VOC/gas
- temperature
- humidity
- timestamp
- freshness label

### B. Sensor calibration

Study:

- baseline
- drift
- humidity effects
- environmental contaminants

### C. Multimodal model

Experiment with:

```text
Vision only
Sensor only
Vision + Sensor
Vision + OCR
Sensor + OCR
Vision + Sensor + OCR
```

### D. Fusion strategies

Compare:

- early fusion
- feature-level fusion
- late fusion
- learned fusion

### E. Shelf-life regression

Evaluate:

- Random Forest
- XGBoost
- neural regression
- possibly LSTM for time-series sensor data

### F. Ablation study

Measure whether each modality contributes useful information.

### G. Explainable AI

Implement Grad-CAM or suitable equivalent.

### H. Edge deployment

Investigate:

- ONNX
- TensorFlow Lite where appropriate
- quantization
- Raspberry Pi
- ESP32-assisted sensing

### I. Final evaluation

Report:

- classification metrics
- regression metrics
- latency
- memory
- robustness
- missing-modality performance
- confusion matrices
- ablation results

---

# 39. Academic Research Question

The eventual system should be capable of experimentally answering:

> **Does multimodal fusion of visual appearance, VOC/environmental sensor data, and OCR-derived expiry information improve food freshness assessment and robustness compared with individual or dual-modality approaches?**

A secondary research question:

> **Can the system maintain useful assessment performance when one modality is unavailable or degraded?**

Do not claim these hypotheses are proven until experiments are performed.

---



---

# 42. Mandatory Phase-by-Phase Stability & Testing Gate

**NON-NEGOTIABLE: The project must remain runnable and testable after EVERY development phase.**

Do not implement multiple phases/features continuously and only test everything at the end.

After completing **each phase**, temporarily stop feature development and perform a stability checkpoint.

## Required cycle

```text
PLAN
  ↓
IMPLEMENT
  ↓
RUN
  ↓
TEST
  ↓
FIX
  ↓
RE-RUN
  ↓
VERIFY
  ↓
ONLY THEN → NEXT PHASE
```

A phase is **NOT complete** if the application is broken, cannot start, or previously working functionality has regressed.

## After Every Phase, Verify

### 1. Application startup
- frontend starts successfully
- backend starts successfully
- database connection works
- required migrations work
- no blocking runtime errors exist

### 2. Existing functionality
Re-test all previously completed critical flows. Do not assume previously working functionality is still working.

At minimum, where implemented:

```text
Open application
  ↓
Navigate pages
  ↓
Login/Register
  ↓
Dashboard
  ↓
Scan workflow
  ↓
API communication
  ↓
Database persistence
  ↓
Result page
  ↓
History
```

### 3. Automated tests
Run the relevant test suites after every phase. Use the actual project commands, for example:

```bash
pytest
npm test
npm run build
```

If a test fails:
1. identify the regression/failure
2. fix it
3. run the test again
4. continue only when the relevant tests pass

### 4. Production build
After significant frontend changes, verify that the production build succeeds and has no blocking errors.

### 5. PWA regression check
After every frontend/PWA-related phase verify:
- app loads
- service worker registers
- manifest remains valid
- PWA build succeeds
- installability has not been broken
- cached app shell still works
- offline fallback/state still behaves correctly

Do not accidentally remove or disable PWA functionality while adding React features.

### 6. API verification
After backend/API changes:
- start FastAPI
- verify `/health`
- verify modified endpoints
- verify request validation
- verify database interaction

### 7. Database verification
After schema/database changes:
- run migrations
- verify migration success
- verify startup against the migrated database
- verify affected CRUD operations

Never leave code expecting a schema that has not been migrated.

### 8. Integration verification
When a phase touches multiple layers, test the complete path:

```text
React
  ↓
FastAPI
  ↓
Service
  ↓
ML/OCR
  ↓
Database
  ↓
FastAPI response
  ↓
React UI
```

Do not test only an isolated function when the feature depends on several layers.

---

# 43. Regression Rule

**Never sacrifice an already-working feature to implement a new feature without fixing the regression.**

If a new change breaks something:

```text
NEW FEATURE
    ↓
REGRESSION FOUND
    ↓
STOP
    ↓
FIX REGRESSION
    ↓
RUN RELEVANT TESTS
    ↓
CONTINUE
```

Do not mark a phase complete with known broken core functionality.

---

# 44. Phase Completion Report

At the end of EVERY phase, update `PROJECT_STATUS.md` with:

```text
## Phase X — COMPLETED

Implemented:
- ...

Tests Run:
- ...

Build: PASS / FAIL
Backend: PASS / FAIL
Frontend: PASS / FAIL
Database: PASS / FAIL
PWA: PASS / FAIL / NOT AFFECTED
Integration: PASS / FAIL

Known Issues:
- ...

Next Phase:
- ...
```

Also record important technical decisions, migrations, or known limitations introduced during the phase.

---

# 45. Golden Rule for Development

Treat every completed phase as a **stable checkpoint**. The repository should always remain in a state where another developer can:

```text
clone/open project
      ↓
install dependencies
      ↓
start services
      ↓
run tests
      ↓
use all previously completed functionality
```

The goal is **incremental, verifiable development**, not a large batch of untested code.

### NEVER DO THIS

```text
Phase 1 → Phase 2 → Phase 3 → Phase 4 → Test everything
```

### ALWAYS DO THIS

```text
Phase 1 → TEST → STABLE CHECKPOINT
       ↓
Phase 2 → TEST → STABLE CHECKPOINT
       ↓
Phase 3 → TEST → STABLE CHECKPOINT
       ↓
...
```

If a phase cannot be fully implemented because a dependency is unavailable, keep the project runnable using a clearly documented interface/mock adapter **without pretending that the real functionality has been completed**.


# 40. Agent Operating Procedure

Before writing significant code:

### Step 1
Inspect the current repository thoroughly.

Identify:

- existing frontend
- existing backend
- existing models
- existing assets
- package manager
- current routes
- database
- configuration
- README
- Git status

### Step 2
Do not destroy existing functionality.

Create a migration/refactoring plan.

### Step 3
Establish the architecture.

### Step 4
Implement the 60% milestone in priority order.

### Step 5
After every major milestone:

- run the application
- run tests
- fix errors
- verify API
- verify frontend
- verify database migrations

### Step 6
At the end, provide:

```text
IMPLEMENTED
PARTIALLY IMPLEMENTED
NOT IMPLEMENTED
KNOWN ISSUES
NEXT STEPS
```

### Step 7
Update:

```text
README.md
PROJECT_STATUS.md
ARCHITECTURE.md
PHASES.md
```

---

# 41. Final Instruction to the Coding Agent

You are not being asked to create a superficial college demo.

Build the **first 60% of a credible academic/research software system**.

Prioritize:

1. correctness
2. clean architecture
3. real functionality
4. reproducibility
5. extensibility
6. mobile/PWA usability
7. ML readiness
8. honest documentation

The most important architectural principle is:

```text
                    ONE FOOD SCAN
                         ↓
        ┌────────────────┼────────────────┐
        ↓                ↓                ↓
      VISION            OCR             SENSOR
        ↓                ↓                ↓
   visual evidence  expiry evidence  chemical evidence
        └────────────────┼────────────────┘
                         ↓
                  FUSION / DECISION
                         ↓
                  FINAL ASSESSMENT
                         ↓
                  USER-FACING REPORT
```

Build the system so that the future research work can replace individual components without rewriting the entire application.

**Start by inspecting the existing repository, then implement the Phase-1 60% milestone. Do not ask for permission for routine engineering decisions. Only stop and ask when a decision materially changes the research scope, requires unavailable credentials/hardware, risks deleting existing work, or creates an irreversible architectural choice.**
