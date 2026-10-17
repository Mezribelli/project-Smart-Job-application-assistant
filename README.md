# Smart Job Application Assistant (REF: PRX-2026-01)

An intelligent platform to simplify and automate the job application lifecycle:

- **Automated Opportunity Search & Collection:** Automatically discovers and collects job opportunities matching the user's profile, role preferences, and technical skills.
- **Personalized Documents Generation:** Generates tailored CVs and cover letters adapted to each specific job opportunity.
- **Selenium Browser Automation:** Automatically navigates to external application portals, maps profile fields, and submits applications on behalf of the user using Selenium WebDriver.
- **Interactive Application & Document Dashboard:** Tracks pipeline stages (Draft, Applied, Interviewing, Offered, Rejected) and manages documents sent through a unified workspace.

## Technologies and Tools

- **Spring Boot:** Backend REST API, persistence, validation, matching engine, and automated job collector.
- **Selenium:** Headless browser automation engine for pre-filling and submitting web application forms.
- **React:** Modern, responsive frontend built with Vite, TypeScript, and rich dashboard analytics.
- **AI Service (FastAPI):** Multi-language static analysis, AI-powered Python test generation, isolated test execution with coverage, and an automated unit-test pipeline.
- **AWS Bedrock:** LLM provider (Claude / Llama) for test generation, with an offline baseline fallback.
- **PostgreSQL / SQLAlchemy:** Relational database for jobs, profiles, and persisted analysis runs.

## Prerequisites

- Java 21 or newer
- Maven 3.9 or newer (or the bundled `mvnw` wrapper)
- Node.js 20 or newer and npm
- Python 3.11 or newer
- Docker Desktop with Docker Compose
- (Optional) AWS credentials with Bedrock access for real LLM test generation

## Getting started

1. Copy `.env.example` to `.env` and change local values where needed.
2. Start PostgreSQL:

   ```powershell
   docker compose up -d postgres
   ```

3. Start the backend:

   ```powershell
   cd backend
   .\mvnw.cmd spring-boot:run
   # or on Linux/macOS: ./mvnw spring-boot:run
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
- `GET /api/code/providers`
- `POST /api/code/pipeline`
- `GET /api/code/runs` and `GET /api/code/runs/{id}`

Generated documents start as `DRAFT`; editing returns them to draft status and approval is always explicit. The application dashboard counts applications by status. The automation API is a safe preview contract: it maps supported profile fields, reports unsupported fields, and rejects submissions without `submissionConfirmed=true`. A browser driver can be connected to this contract in the next hardening increment.

## PBI-09 intelligent code-analysis & test agent

The AI service is an intelligent agent for analysing **NeoXam GP** code (C/C++ and
the GP rule language), proposing Python `pytest` unit tests, executing them with an
explicit `OK`/`KO` verdict, and running the whole campaign as an automated pipeline
with results persisted to SQL.

### Capabilities

1. **Multi-language static analysis** — Python (`ast`), C++ (GP platform code), and the
   GP rule DSL; language is auto-detected from the source. Produces functions, classes,
   imports, line count, and a cyclomatic-complexity estimate.
2. **AI test generation** — powered by **AWS Bedrock** (Claude / Llama) when configured,
   with a deterministic offline baseline as fallback. The response always records which
   provider/model produced the suite and whether a fallback occurred.
3. **Manual execution** — runs the suite in an isolated subprocess with a timeout and
   returns `OK`/`KO`, the exit code, the raw `pytest` output, and line coverage.
4. **Automated pipeline** — one call chains analyze → generate → execute → persist and
   returns a per-stage report.
5. **SQL persistence** — every run is stored (SQLite by default, PostgreSQL via
   `AI_DATABASE_URL`) and exposed through the run-history endpoints.

### Example (PowerShell)

```powershell
$body = @{ source = "def add(left, right):`n    return left + right"; language = "python" } | ConvertTo-Json
Invoke-RestMethod http://localhost:8000/api/code/generate-tests -Method Post -ContentType "application/json" -Body $body
```

### Automated pipeline CLI

The same pipeline used by the API and CI:

```powershell
cd ai-service
.\.venv\Scripts\python.exe run_pipeline.py samples\gp_sample.cpp
.\.venv\Scripts\python.exe run_pipeline.py samples\gp_rule_sample.gp
.\.venv\Scripts\python.exe run_pipeline.py samples\solution.py
```

### AWS Bedrock configuration

| Variable          | Purpose                                    | Default                                        |
| ----------------- | ------------------------------------------ | ---------------------------------------------- |
| `BEDROCK_MODEL_ID`| Model / inference profile id               | `anthropic.claude-3-5-sonnet-20240620-v1:0`    |
| `AWS_REGION`      | Bedrock region (`AWS_DEFAULT_REGION` alias) | `us-east-1`                                    |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | Credentials (or use an instance profile) | —                        |

When Bedrock is not configured (or fails), the agent transparently falls back to the
offline baseline so the pipeline never blocks. The UI badges which provider is active.

### Subject requirement mapping

| Requirement (NeoXam subject)                       | Implementation                                                        |
| -------------------------------------------------- | --------------------------------------------------------------------- |
| Analyse GP back-office code (C/C++ + rule DSL)     | `ai-service/app/analyzers/{cpp,gp}_analyzer.py`, auto-detection in `detector.py` |
| Propose Python unit tests                          | `ai-service/app/generator.py` + `app/llm/bedrock_provider.py` / `local_provider.py` |
| Execute unit tests, report OK / KO                 | `ai-service/app/executor.py`                                          |
| Automated test pipeline                            | `ai-service/app/pipeline.py`, `/api/code/pipeline`, `.github/workflows/ci.yml` |
| Python                                             | Entire `ai-service` (FastAPI, pytest, SQLAlchemy)                     |
| AWS Bedrock (Claude / Llama)                       | `ai-service/app/llm/bedrock_provider.py` (fallback to local)          |
| SGBD / SQL                                         | `ai-service/app/persistence.py` (SQLAlchemy: SQLite / PostgreSQL)     |

> Execute only trusted code in an isolated development environment.

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
