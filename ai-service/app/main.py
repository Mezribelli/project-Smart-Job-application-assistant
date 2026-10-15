import os
from subprocess import TimeoutExpired

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .code_agent import CodeAnalysisError, analyze_source, execute_tests, generate_tests
from .schemas import SourceRequest, TestExecutionRequest

app = FastAPI(
    title="Smart Job AI Service",
    version="0.0.1",
    description="AI capabilities for the Smart Job Application Assistant.",
)

DEFAULT_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]


def allowed_origins() -> list[str]:
    """Local development origins, plus the sandbox preview origin when Base44 runs this service.

    The preview serves the frontend from https://3000-<public host suffix>, a different site from
    this service, so that origin has to be allowed. Gated on BASE44_PREVIEW_MODE being exactly "1";
    when the flag is absent or anything else, the allowlist keeps its original behaviour.
    """
    origins = list(DEFAULT_ORIGINS)
    if os.environ.get("BASE44_PREVIEW_MODE") == "1":
        suffix = os.environ.get("BASE44_PUBLIC_HOST_SUFFIX", "").strip()
        if suffix:
            origins.append(f"https://3000-{suffix}")
    return origins


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "UP", "service": "ai-service"}


@app.post("/api/code/analyze")
def analyze(request: SourceRequest) -> dict[str, object]:
    try:
        return analyze_source(request.source)
    except CodeAnalysisError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/code/generate-tests")
def generate(request: SourceRequest) -> dict[str, object]:
    try:
        analysis, tests = generate_tests(request.source)
        return {"analysis": analysis, "testSource": tests}
    except CodeAnalysisError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/code/execute-tests")
def execute(request: TestExecutionRequest) -> dict[str, object]:
    try:
        return execute_tests(request.test_source)
    except CodeAnalysisError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except TimeoutExpired as error:
        raise HTTPException(status_code=408, detail="Test execution exceeded 15 seconds") from error
