"""FastAPI application for the GP code-analysis & test-generation agent.

Endpoints
---------
GET  /health                     liveness probe
GET  /api/code/providers         available test-generation providers
POST /api/code/analyze           structural analysis of GP/Python/C++ source
POST /api/code/generate-tests    propose a Python pytest suite (Bedrock or local)
POST /api/code/execute-tests     run a suite manually and get OK/KO + coverage
POST /api/code/pipeline          run the full automated pipeline (SQL persisted)
GET  /api/code/runs              history of pipeline runs (from the database)
GET  /api/code/runs/{run_id}     one stored run
"""

from subprocess import TimeoutExpired

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import persistence
from .analyzers import analyze
from .errors import CodeAnalysisError, UnsupportedLanguageError
from .executor import execute_test_source
from .generator import generate_suite
from .llm.factory import provider_status
from .pipeline import run_pipeline
from .schemas import PipelineRequest, SourceRequest, TestExecutionRequest

app = FastAPI(
    title="Smart Job AI Service",
    version="0.2.0",
    description=(
        "Intelligent agent that analyses NeoXam GP code, proposes Python unit "
        "tests, executes them manually (OK/KO) and can run a full automated "
        "pipeline. Test generation is powered by AWS Bedrock when configured, "
        "with an offline baseline fallback."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "UP", "service": "ai-service"}


@app.get("/api/code/providers")
def providers() -> dict[str, object]:
    return {"providers": provider_status()}


@app.post("/api/code/analyze")
def analyze_endpoint(request: SourceRequest) -> dict[str, object]:
    try:
        return analyze(request.source, request.language)
    except CodeAnalysisError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/code/generate-tests")
def generate_endpoint(request: SourceRequest) -> dict[str, object]:
    try:
        return generate_suite(request.source, language=request.language)
    except CodeAnalysisError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/code/execute-tests")
def execute_endpoint(request: TestExecutionRequest) -> dict[str, object]:
    try:
        language = None if request.language == "auto" else request.language
        return execute_test_source(request.test_source, request.source, language)
    except CodeAnalysisError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except TimeoutExpired as error:
        raise HTTPException(status_code=408, detail="Test execution exceeded the time limit") from error


@app.post("/api/code/pipeline")
def pipeline_endpoint(request: PipelineRequest) -> dict[str, object]:
    try:
        return run_pipeline(
            request.source,
            language=request.language,
            provider=request.provider,
            execute=request.execute,
            persist=request.persist,
        )
    except UnsupportedLanguageError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except CodeAnalysisError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/api/code/runs")
def runs_endpoint(limit: int = 20) -> dict[str, object]:
    limit = max(1, min(limit, 100))
    return {"runs": persistence.list_runs(limit)}


@app.get("/api/code/runs/{run_id}")
def run_endpoint(run_id: int) -> dict[str, object]:
    run = persistence.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return run
