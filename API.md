# API (`/api/v1`, OpenAPI at `/docs`)

- `GET /health` → `{status}`
- `POST /auth/register` `{email, password(min 6, max 72)}` → 201 `{access_token, token_type, user}` (auto-login; extra fields ignored) · `POST /auth/login` → `{access_token, token_type, user}` · `GET /auth/me` (Bearer)
- `POST /scans` (Bearer, multipart `image` ≤10MB verified via PIL + optional `food_type, temperature_c, humidity_pct, voc_index, notes`) → full assessment + persisted IDs
- `GET /scans` · `GET /scans/{id}` · `DELETE /scans/{id}`
- `POST /predictions/vision` (multipart image) → `{food_type, freshness, confidence, model_version, model_type: prototype}`
- `POST /ocr/extract` (multipart image or `{text}`) → `{date_detected, expiry_date, days_remaining, ...}` never fabricated
- `POST /sensors/readings` `{gas_value, temperature, humidity, device_id?, scan_id?}` · `GET /sensors/readings`
- `POST /assessments` · `GET /assessments/{scan_id}`
