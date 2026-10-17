from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

PYTHON_SOURCE = "def add(a: int, b: int) -> int:\n    return a + b\n"
CPP_SOURCE = "#include <cmath>\nnamespace gp {\ndouble f(double x) { if (x > 0) { return x; } return 0.0; }\n}\n"


def test_providers_endpoint() -> None:
    response = client.get("/api/code/providers")

    assert response.status_code == 200
    providers = response.json()["providers"]
    names = {p["provider"] for p in providers}
    assert {"bedrock", "local"} <= names


def test_analyze_endpoint_detects_language() -> None:
    response = client.post("/api/code/analyze", json={"source": CPP_SOURCE})

    assert response.status_code == 200
    assert response.json()["language"] == "cpp"


def test_analyze_endpoint_rejects_invalid_python() -> None:
    response = client.post("/api/code/analyze", json={"source": "def bad(:", "language": "python"})

    assert response.status_code == 400


def test_generate_tests_endpoint() -> None:
    response = client.post("/api/code/generate-tests", json={"source": PYTHON_SOURCE})

    assert response.status_code == 200
    body = response.json()
    assert "testSource" in body
    assert body["provider"] == "local"


def test_execute_tests_endpoint_ok_and_ko() -> None:
    generated = client.post("/api/code/generate-tests", json={"source": PYTHON_SOURCE}).json()
    ok = client.post(
        "/api/code/execute-tests",
        json={"test_source": generated["testSource"], "source": PYTHON_SOURCE, "language": "python"},
    )
    assert ok.status_code == 200
    assert ok.json()["status"] == "OK"

    ko = client.post("/api/code/execute-tests", json={"test_source": "def test_x():\n    assert 1 == 2\n"})
    assert ko.json()["status"] == "KO"


def test_pipeline_endpoint_and_history() -> None:
    response = client.post("/api/code/pipeline", json={"source": CPP_SOURCE, "provider": "local"})

    assert response.status_code == 200
    body = response.json()
    assert body["execution"]["status"] == "OK"
    assert body["runId"] is not None

    history = client.get("/api/code/runs")
    assert history.status_code == 200
    assert any(run["id"] == body["runId"] for run in history.json()["runs"])

    single = client.get(f"/api/code/runs/{body['runId']}")
    assert single.status_code == 200
    assert single.json()["language"] == "cpp"


def test_missing_run_returns_404() -> None:
    assert client.get("/api/code/runs/99999999").status_code == 404
