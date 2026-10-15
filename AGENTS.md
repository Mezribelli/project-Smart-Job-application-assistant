# Working in this repository (Base44 sandbox)

## Running the stack

```bash
docker compose -f docker-compose.base44.yml up -d
docker compose -f docker-compose.base44.yml ps
curl -s http://localhost:3000/ | head
```

Four services, all run from the cloned source (no prebuilt application images):

| service    | image                          | host port | notes                                  |
| ---------- | ------------------------------ | --------- | -------------------------------------- |
| postgres   | postgres:16-alpine             | –         | internal only, `smart_jobs` database   |
| backend    | maven:3.9-eclipse-temurin-21   | –         | `mvn spring-boot:run` on 8080          |
| ai-service | python:3.12-slim               | –         | uvicorn `--reload` on 8000             |
| frontend   | node:22                        | 3000      | Vite dev server on 5173                |

The first `up` is slow (Maven, npm and pip download dependencies into named volumes:
`backend-maven-repo`, `frontend-node-modules`, `ai-service-pip-cache`). Later starts are fast.

## No external credentials are needed

PostgreSQL, the API and the AI service all run locally. Matching uses a deterministic
skill-overlap score and the code agent is AST-based, so there is no AI provider key to set.
The database credentials in `docker-compose.base44.yml` are dev-only values for the local
container, not user secrets.

## Non-obvious setup details

- `backend/src/main/resources/application.yml` hardcodes `jdbc:postgresql://localhost/...`,
  which cannot resolve the `postgres` compose service. The compose file overrides the
  datasource through Spring's relaxed binding (`SPRING_DATASOURCE_URL/USERNAME/PASSWORD`)
  instead of editing the shared config. Keep that override in place if the DB wiring changes.
- Hibernate `ddl-auto: update` creates the schema on boot — no migration or seed step.
- The preview uses a single origin: the browser only reaches port 3000 and Vite proxies
  `/api` to `http://backend:8080`. `VITE_API_BASE_URL` is set to an empty string in the
  sandbox, which makes the app request `/api` on its own origin; the proxy is registered
  only when `BASE44_PREVIEW_MODE=1` (see `frontend/vite.config.ts`), so outside the sandbox
  the app keeps using the absolute `VITE_API_BASE_URL`. No backend CORS change was needed
  because the browser never issues a cross-origin request here.
- Browsers attach an `Origin` header to POST/PUT/PATCH/DELETE even when the request looks
  same-origin, and Spring rejects any origin that is not on the controllers' `@CrossOrigin`
  list (403 with an empty body, which the frontend shows as "Request failed"). The list is
  now read from configuration: `app.cors.allowed-origins` defaults to `http://localhost:5173`
  (unchanged for local development) and `app.cors.sandbox-origin` defaults to empty.
  `docker-compose.base44.yml` sets both for the sandbox (preview origin + host port 3000), so
  an unset property keeps the original behaviour anywhere else. If a write returns 403 in the
  preview, check those two values first.
- `Profile.skills` and `JobOffer.skills` are `@ElementCollection(fetch = FetchType.EAGER)`.
  They used to be lazy, and because `spring.jpa.open-in-view` is `false` Hibernate serialized
  them after the session closed — every read of a saved profile or job offer failed with
  HTTP 500 (`failed to lazily initialize a collection ... no Session`). Keep them eager (or
  move the read into a transaction) if the fetch strategy is revisited.
- `ai-service` is intentionally not published to a host port: `POST /api/code/execute-tests`
  executes submitted Python code. Reach it from the host with
  `docker compose -f docker-compose.base44.yml exec ai-service curl -s localhost:8000/health`.
- Java does not hot reload (spring-boot-devtools is not a project dependency). After editing
  a `.java` file run `docker compose -f docker-compose.base44.yml restart backend`; the frontend
  and AI service reload on their own.

## Verifying it works

- `GET http://localhost:3000/` serves the React app (Vite). Through the proxy,
  `GET http://localhost:3000/api/health` must return `{"status":"UP","service":"backend"}`.
- `docker compose -f docker-compose.base44.yml ps` should show all four services healthy.
- Writes work end to end: saving a profile and adding a job offer from the UI persist to
  PostgreSQL and read back with their skills intact.
- Tests: `docker compose -f docker-compose.base44.yml exec backend mvn test` (H2 profile) and
  `docker compose -f docker-compose.base44.yml exec ai-service python -m pytest`.
