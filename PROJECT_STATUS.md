# FreshSense AI — current prototype status

FreshSense is a working student-demo application for package reading, scan evidence, and household batch tracking. It is not a certified food-safety system, and model estimates are not calibrated probabilities.

## Implemented workflow

- Account sign-in and user-scoped scan history.
- Mobile camera/upload scanning with image framing and retake guidance.
- Common raster image uploads normalized to JPEG for display/analysis while retaining the private original, with EXIF orientation and transparency handled consistently; fast OCR first pass with enhanced retries for difficult stamps.
- Package OCR/date parsing and product-category recognition with visible evidence and source.
- OCR regression coverage for the four bundled package-photo examples (month/year, numeric expiry, textual month, and use-by date); these are synthetic demonstration cases, not an independent accuracy benchmark.
- User review for dates and categories when recognition is incomplete or needs correction.
- Freshness Passport evidence, limitations, conflicts, and repeat-scan timeline.
- Rule-based Evidence Recovery Loop that prioritizes a scan's missing or conflicting evidence and offers a corresponding manual review or follow-up action.
- Pantry batches with quantity, package-date provenance, storage location, opened date, notes, and optional reminder window.
- Date watch, explainable use-next sorting, in-app reminder queue, and opt-in browser alerts while FreshSense is open.
- SQLite local-demo startup and Alembic migrations for PostgreSQL.
- Free-port-aware PC/phone launcher and a presentation checklist.
- Local package-label manifest template and held-out category/date evaluation script.

## Verification in the latest implementation pass

- Frontend TypeScript check: passed.
- Frontend production/PWA build: passed.
- Frontend UI tests: 4 passed.
- Backend Python syntax compilation: passed.
- OCR smoke against all four bundled synthetic package photos: expected labels and dates extracted; about 0.5–2.4 seconds per image on the development PC.
- Package-label evaluation CLI help/import: passed.
- Backend pytest integration suite and live database migrations: not run in this pass; the local Python environment is missing `PyJWT`, and the local Docker engine was unavailable. CI provisions PostgreSQL and now installs Tesseract to exercise the package-photo regressions.
- Phone hardware smoke test: documented, but not performed on a physical phone in this pass.

## Known research and runtime limits

- Vision output remains a prototype and is not validated for safety decisions.
- Tesseract must be installed on the backend computer for OCR. The production API image includes it; EasyOCR remains an optional retry path in development installs.
- No package-label validation benchmark has been collected. Use the local manifest and evaluation workflow before reporting accuracy.
- The existing produce image candidate scored 52.6% on its limited held-out dataset and remains inactive; see `data/README.md` and `NOVELTY.md`.
- Browser reminders are checked while the app is open. They are not delivered while the browser/app is closed.
- Temperature, humidity, and VOC demo values are illustrative unless entered from an actual calibrated sensor.
- No learned multimodal fusion, shelf-life regression, or calibrated ESP32 hardware model is currently implemented.
- The Evidence Recovery Loop is a transparent workflow rule, not a trained AI model, proven novelty, or a safety recommendation.

## Next research phase

Collect permissioned, varied package photos and controlled repeated observations; keep package/item groups separated across training and evaluation; calibrate sensors; evaluate OCR, category, and fusion performance on untouched groups; then consider a trained lightweight model and background notification infrastructure.
