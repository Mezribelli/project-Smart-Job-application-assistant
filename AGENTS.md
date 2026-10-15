# AGENTS.md — Smart Job Application Assistant

Three services: Spring Boot backend (`backend/`), FastAPI AI service (`ai-service/`), React + Vite
frontend (`frontend/`), plus PostgreSQL. The repository's own `docker-compose.yml` only defines
PostgreSQL for a manually installed toolchain; the reproducible stack is
`docker-compose.base44.yml`.

## Running everything (one command)

```bash
docker compose -f docker-compose.base44.yml up -d --build
```

| Service | Host port | Notes |
| --- | --- | --- |
| frontend (Vite dev server) | 3000 | the user-facing entry point |
| backend (Spring Boot) | 8080 | `GET /api/health` |
| ai-service (uvicorn --reload) | 8000 | `GET /health` |
| postgres | not published | internal only, `smart_jobs` |

## Things that are easy to get wrong

- **Database host.** `application.yml` defaults the datasource to `localhost`; inside compose the
  database is the `postgres` service. `docker-compose.base44.yml` overrides it with
  `SPRING_DATASOURCE_URL`.
- **Backend has no hot reload** (`spring-boot-devtools` is not a dependency). After a Java change:
  `docker compose -f docker-compose.base44.yml restart backend`, then wait for
  `curl -s localhost:8080/api/health` to answer. Frontend and AI service reload on their own
  (Vite HMR / uvicorn `--reload`).
- **CORS lives in one place.** `config/WebConfig.java` (backend) and `allow_origins()` in
  `ai-service/app/main.py` are the only allowlists. Do not put `@CrossOrigin` back on a controller:
  a handler-level annotation overrides the global mapping and pins the API to that one origin.
- **Sandbox preview origin.** The preview serves the frontend from `https://3000-<public host
  suffix>`, a different site from the API ports, so both allowlists append that origin when
  `BASE44_PREVIEW_MODE` is exactly `"1"` (only `BASE44_PREVIEW_MODE` and
  `BASE44_PUBLIC_HOST_SUFFIX` are read). With the flag unset or any other value the allowlist is
  the original `http://localhost:5173` / `http://127.0.0.1:5173`. The frontend exports
  `VITE_API_BASE_URL` / `VITE_AI_SERVICE_URL` from the same suffix at container start, and Vite
  accepts the proxied host through `__VITE_ADDITIONAL_SERVER_ALLOWED_HOSTS`.
- **Application status vocabulary.** `ApplicationStatus` values must stay in sync with the
  dashboard select in `frontend/src/main.tsx`, the `status-*` classes in `frontend/src/styles.css`
  and the README: `DRAFT, READY_TO_APPLY, APPLIED, INTERVIEWING, OFFERED, REJECTED`. Hibernate
  generates a `job_applications_status_check` CHECK constraint from the enum and `ddl-auto: update`
  never alters it, so a **database created before an enum change keeps rejecting the new values**
  (`409 Database constraint violation`). Recreate the dev database after such a change:
  `docker compose -f docker-compose.base44.yml down && docker volume rm app_postgres-data`, or drop
  the stale constraint by hand. A fresh database gets the correct constraint.
- **Selenium** (`SeleniumAutomationService.createHeadlessDriver`) only looks for Chrome/Edge
  binaries under the Windows install paths. On Linux the driver is `null`, so `selenium-apply`
  returns the simulated report instead of driving a browser. The `example.com` URL in the UI is
  treated as a mock and never launches a driver. `Form Automation` is otherwise usable (field
  mapping preview is real).
- **No secrets.** Nothing outside compose is required: no `.env`, no external credentials, no
  cloud provider. `.env.example` only carries local port/database values.

## Verifying

```bash
# service health
curl -s localhost:8080/api/health && curl -s localhost:8000/health

# backend tests (H2, no database needed) — no JDK on the sandbox host:
docker run --rm -v /app/backend:/app -w /app -v /root/.m2:/root/.m2 \
  maven:3.9-eclipse-temurin-21 mvn -q test

# AI service tests — no python3-venv on the sandbox host:
docker run --rm -v /app/ai-service:/app -w /app python:3.12-slim \
  sh -c "pip install -q -r requirements.txt && python -m pytest -q"
```

End-to-end in the UI: save a profile in **My Profile**, press **Auto-Collect Matching Jobs** (score
badges appear), generate and approve a CV in **Documents Studio**, **Track Application** then move
its stage in **Applications Board**, and in **AI Code Studio** run `Run AST Analysis` →
`Generate pytest Baseline` → `Execute Tests Now` (expects `STATUS: OK`).
