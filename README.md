# Smart Job Application Assistant

Foundation for the Smart Job Application Assistant (PBI-01) with PBIs 02–05 implemented.

## Architecture

- `frontend/`: React application built with Vite.
- `backend/`: Spring Boot REST API.
- `ai-service/`: Python service reserved for matching, document generation, and code analysis.
- PostgreSQL: local development database managed by Docker Compose.

## Prerequisites

- Java 21 or newer
- Maven 3.9 or newer
- Node.js 20 or newer and npm
- Python 3.11 or newer
- Docker Desktop with Docker Compose

The current environment does not have Node.js, Maven, or Docker installed yet. Install those tools before running the full stack.

## Getting started

1. Copy `.env.example` to `.env` and change local values where needed.
2. Start PostgreSQL:

   ```powershell
   docker compose up -d postgres
   ```

3. Start the backend:

   ```powershell
   cd backend
   mvn spring-boot:run
   ```

4. Start the AI service:

   ```powershell
   cd ai-service
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```

5. Install and start the frontend:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

## Health checks

- Backend: `GET http://localhost:8080/api/health`
- AI service: `GET http://localhost:8000/health`
- Frontend: `http://localhost:5173`

## Implemented APIs

- `POST/GET /api/profiles`
- `GET/PUT /api/profiles/{id}`
- `POST/GET /api/jobs`
- `GET/PUT/DELETE /api/jobs/{id}`
- `PATCH /api/jobs/{id}/status?value=SAVED`
- `GET /api/matching/profiles/{profileId}/jobs/{jobId}`

The matching endpoint currently uses a deterministic skill-overlap score. This provides a reliable baseline before adding an external AI provider.

## PBIs 06–08 APIs

- `POST /api/documents/generate?profileId={id}&jobId={id}&type=CV|COVER_LETTER`
- `GET /api/documents?profileId={id}`
- `PUT /api/documents/{id}` and `POST /api/documents/{id}/approve`
- `POST /api/applications?profileId={id}&jobId={id}`
- `GET /api/applications?profileId={id}`
- `GET /api/applications/dashboard?profileId={id}`
- `PATCH /api/applications/{id}`
- `POST /api/automation/preview?profileId={id}&url={url}`
- `POST /api/automation/submit`
- `POST /api/code/analyze`
- `POST /api/code/generate-tests`
- `POST /api/code/execute-tests`

Generated documents start as `DRAFT`; editing returns them to draft status and approval is always explicit. The application dashboard counts applications by status. The automation API is a safe preview contract: it maps supported profile fields, reports unsupported fields, and rejects submissions without `submissionConfirmed=true`. A browser driver can be connected to this contract in the next hardening increment.

## PBI-09 code-analysis agent

The AI service accepts Python source code and provides:

1. AST-based function, class, import, and line analysis.
2. A generated `pytest` baseline that must be reviewed before use.
3. Manual test execution with a 15-second timeout and an explicit `OK` or `KO` result.

Example:

```powershell
$body = @{ source = "def add(left, right):`n    return left + right" } | ConvertTo-Json
Invoke-RestMethod http://localhost:8000/api/code/generate-tests -Method Post -ContentType "application/json" -Body $body
```

This local baseline does not silently claim AI-generated quality. AWS Bedrock can replace or enrich the generation step later, behind the same response contract. Execute only trusted code in an isolated development environment.

## PBI-10 security and delivery baseline

- Local secrets are supplied through environment variables and ignored by Git.
- API error responses do not include Spring's internal exception message by default.
- Request validation and explicit confirmation protect document and automation workflows.
- Multipart request sizes are capped at 5 MB per file and 10 MB per request.
- Backend tests use an in-memory H2 database configuration.
- Python unit tests cover health, AST analysis, generation, and invalid input.

## PBIs 02–05 definition of done

- Profile creation, retrieval, and update are implemented with validation.
- Job offers can be created, searched, filtered, updated, status-managed, and deleted.
- The React interface supports profile editing and keyword search.
- Job/profile data is persisted through PostgreSQL.
- Job matching returns a score, matching skills, missing skills, and a recommendation.

## PBI-01 definition of done

- The repository contains separate frontend, backend, and AI-service applications.
- PostgreSQL has a repeatable local Docker Compose definition.
- The backend and AI service expose health checks.
- Local secrets are excluded from Git.
- Setup and launch steps are documented.
