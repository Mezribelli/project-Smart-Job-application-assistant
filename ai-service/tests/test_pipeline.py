from app.pipeline import run_pipeline

PYTHON_SOURCE = "def add(a: int, b: int) -> int:\n    return a + b\n"
CPP_SOURCE = "#include <cmath>\nnamespace gp {\ndouble f(double x) { if (x > 0) { return x; } return 0.0; }\n}\n"
GP_SOURCE = "RULE ComputeNav(fund_id)\n    SELECT sum(v) FROM positions;\nEND\n"


def test_pipeline_python_end_to_end_persists_run() -> None:
    report = run_pipeline(PYTHON_SOURCE, provider="local")

    assert report["analysis"]["language"] == "python"
    assert report["execution"]["status"] == "OK"
    assert report["runId"] is not None
    stage_names = [stage["stage"] for stage in report["stages"]]
    assert "generate" in stage_names
    assert "execute" in stage_names
    assert "persist" in stage_names


def test_pipeline_cpp_end_to_end() -> None:
    report = run_pipeline(CPP_SOURCE, provider="local")

    assert report["analysis"]["language"] == "cpp"
    assert report["execution"]["status"] == "OK"


def test_pipeline_gp_end_to_end() -> None:
    report = run_pipeline(GP_SOURCE, provider="local")

    assert report["analysis"]["language"] == "gp"
    assert report["execution"]["status"] == "OK"


def test_pipeline_without_execution_or_persistence() -> None:
    report = run_pipeline(PYTHON_SOURCE, provider="local", execute=False, persist=False)

    assert report["execution"] is None
    assert report["runId"] is None
