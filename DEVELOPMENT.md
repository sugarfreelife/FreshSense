# DEVELOPMENT
- Backend: `cd backend && pip install -r requirements.txt`; configure `DATABASE_URL`, `TEST_DATABASE_URL` (a separate hosted database ending in `_test`), and a random `JWT_SECRET` of at least 32 characters in `backend/.env`; run `alembic upgrade head`, `python -m pytest tests -q`, then `uvicorn app.main:app --reload`.
- Frontend: `cd frontend && npm install && npm run build && npm run dev`
- DB: PostgreSQL is the application database. Set `DATABASE_URL` in `backend/.env` and ensure the database/user exist before running `alembic upgrade head`. The API does not create or migrate tables on startup; Alembic owns schema changes.
- Existing DB: if it already has the exact initial schema created by an earlier app startup, run `alembic stamp head` once instead of `alembic upgrade head`; back up and reconcile any other existing schema before migrating.
- PWA: `npm run build` generates `sw.js`; test installability in Chrome desktop/Android; offline shows cached shell + "Connection required for AI analysis".
- Tests: backend tests use a dedicated PostgreSQL database named `freshsense_test`, reset between tests; frontend tests use Vitest with `npm test -- --run`.
