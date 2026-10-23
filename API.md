# API (`/api/v1`, OpenAPI at `/docs`)

- `GET /health` → `{status}`
- `POST /auth/register` `{email, name?, password(min 6, max 72)}` → 201 `{access_token, token_type, user}` · `POST /auth/login` → `{access_token, token_type, user}` · `GET /auth/me` (Bearer)
- `POST /scans` (Bearer, multipart field `file` ≤10MB verified via PIL; optional `food_type, temperature_c, humidity_pct, voc_index, notes, tracked_item_id, new_item_name`) → full assessment + persisted IDs
- `GET /scans?limit=20&offset=0` → scan array with `X-Total-Count` header · `GET /scans/{id}` · `DELETE /scans/{id}` · `GET /scans/{id}/image` (Bearer, private image)
- `GET /scans/items` → this user's tracked items and scan counts · `GET /scans/items/{item_id}` → chronological scans for a longitudinal Passport
- `GET /inventory` → this user's purchase batches, sorted by package date · `POST /inventory` `{product_name, category?, quantity, expiry_date?, expiry_source, reminder_days_before?, storage_location?, opened_date?, storage_notes?, source_scan_id?}` → save a batch · `PATCH /inventory/{id}` → edit a batch's name, category, quantity, date, reminder, or storage context · `DELETE /inventory/{id}`
- `POST /predictions/vision` (multipart image) → `{food_type, freshness, confidence, model_version, model_type: prototype}`
- `POST /ocr/extract` (multipart field `file`) → OCR result; dates are never fabricated · `POST /ocr/parse-text` `{text}` → parse manually supplied label text
- `POST /sensors/readings` `{gas_value, temperature, humidity, device_id?, scan_id?}` · `GET /sensors/readings`
- `POST /assessments` · `GET /assessments/{scan_id}`
