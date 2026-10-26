# Production deployment and release checks

## What the container stack provides

- PostgreSQL with a persistent Compose volume; the database port is not published to the host.
- API migrations applied with Alembic before the API process starts.
- Private image uploads stored on a persistent volume and served only through authenticated API routes.
- A Python 3.12 production dependency lock that keeps training/test tools and neural OCR out of the runtime image. Tesseract is installed in the API image for local OCR.
- The API container runs as an unprivileged user; its upload volume is writable only by the service account.
- A static PWA served by Nginx, with SPA route fallback, same-origin `/api/` proxying, content security policy, and basic browser security headers.
- Production settings reject SQLite and wildcard or non-HTTPS CORS origins. API documentation routes are disabled in production.
- Browser authentication uses an HttpOnly, Secure, SameSite session cookie in production; state-changing cookie-authenticated requests require a matching CSRF token. The web client does not store access tokens in local storage.

## First deployment

1. Put the repository on a server with Docker Engine and the Compose plugin.
2. Copy `production.env.example` to `.env.production`. Replace every sample value. Keep this file private and outside Git.
   - Use a distinct 64-character random hexadecimal value for `POSTGRES_PASSWORD` so it is safe inside the database URL.
   - Use a different random `JWT_SECRET` of at least 32 characters.
   - Set `CORS_ORIGINS` to the exact HTTPS app origin, such as `https://freshsense.example.com`.
3. Put a TLS reverse proxy in front of the Compose web port. Forward the original host, the true client `X-Forwarded-For`, and `X-Forwarded-Proto`; overwrite untrusted client-supplied forwarding headers at that edge and set a request body limit of at least 11 MB. The API port is intentionally unpublished; its Uvicorn process trusts proxy headers only on the private Compose network.
4. Run `docker compose --env-file .env.production up --build -d`.
5. Check the Compose health state, `https://your-domain.example/api/v1/health`, and the sign-in page.
6. Sign in with a newly created account. Local demo accounts are intentionally not seeded into the production PostgreSQL database.

The API uses one container instance and one persistent upload volume. Before increasing replicas, move uploads to shared object storage and add a shared rate-limit/session strategy. Use encrypted, off-host backups for both the PostgreSQL and upload volumes and rehearse a restore.

## Continuous integration

`.github/workflows/ci.yml` runs frontend tests, type checks, production builds, and npm dependency auditing; backend migrations and tests against PostgreSQL plus a Python dependency audit; and builds both production images. A passing CI run verifies the checked-in build and test gates, but does not replace staging, backup-restore, security, or food-label accuracy checks.

## Release checks

- [ ] Confirm the database and upload volumes are backed up and restorable.
- [ ] Apply each Alembic migration to a staging copy before production.
- [ ] Register a new account, sign in, scan a package, inspect OCR text, save a batch, edit its quantity and date, and confirm the authenticated package photo stays private.
- [ ] Try an unreadable label and verify the person can enter or skip the date without a fabricated value.
- [ ] Test camera capture on an HTTPS phone browser and test offline shell behavior.
- [ ] Verify CORS only allows the exact application origin and that docs/OpenAPI routes are disabled.
- [ ] Configure TLS, DNS, firewall rules, backups, log retention, error monitoring, and an uptime alert with the hosting provider.
- [ ] Collect package-label validation data and report OCR/category metrics with held-out products before making recognition claims.

## Known product limits before a commercial launch

- Vision is still an uncalibrated prototype heuristic/model score and must not be used as a food-safety decision.
- Package OCR and category recognition need a documented, held-out package-label evaluation. The production image uses Tesseract; unclear dates must be checked or entered by the user.
- Business workspaces share stock and scan records with explicit owner/manager/staff membership. Members must already have a FreshSense account; invite emails/acceptance, ownership transfer, supplier records, and consolidated cross-location reporting are not implemented. Stock location is currently a free-text branch/area field.
- Browser reminders run while the app is open. Background push/email/SMS delivery, billing, support operations, privacy/retention policy, and account recovery need a real service and owner before commercial operation.
- The deployment stores uploads on one persistent disk volume. Multi-instance deployment requires shared object storage and a retention/deletion policy.
- Registration and sign-in have per-process IP request limits, and scan analysis has a per-user/IP limit. These counters reset on restart and do not coordinate across replicas; add a shared limiter before scaling. Security still needs an independent review, including session invalidation, password recovery, and incident response. Logout clears the browser cookie; issued JWTs are not individually revoked and remain valid until their expiry.
- Dependency audit on 2026-10-26: `npm audit` and `pip-audit` report zero known vulnerabilities for the frontend and locked Python 3.12 backend dependencies. Backend packages are pinned in `backend/requirements-production.lock`; refresh the lock whenever `requirements-production.txt` changes and review the resulting versions before release.
- The Python lock pins versions but does not include package hashes. Add hash checking and automate dependency review in CI before a commercial launch.
