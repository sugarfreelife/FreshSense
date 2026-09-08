# DEVELOPMENT
- Backend: `cd backend && pip install -r requirements.txt && python -m pytest tests -q && uvicorn app.main:app --reload`
- Frontend: `cd frontend && npm install && npm run build && npm run dev`
- DB: default SQLite `freshsense.db`; set `DATABASE_URL=postgresql://...` for Postgres; Alembic (`alembic.ini`) for migrations, `Base.metadata.create_all` on startup for dev.
- PWA: `npm run build` generates `sw.js`; test installability in Chrome desktop/Android; offline shows cached shell + "Connection required for AI analysis".
- Tests: `pytest` (25 backend tests) · `npm test -- --run` (frontend vitest).
