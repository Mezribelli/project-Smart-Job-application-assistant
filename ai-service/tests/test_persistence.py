from app import persistence


def _configure(tmp_path):
    persistence.configure(f"sqlite:///{(tmp_path / 'runs.db').as_posix()}")


def test_save_list_and_get_run(tmp_path) -> None:
    _configure(tmp_path)

    saved = persistence.save_run(
        language="python",
        provider="local",
        model=None,
        analysis={"functions": ["add"], "classes": [], "complexity": 1},
        test_source="def test_add(): pass\n",
        source="def add(a, b):\n    return a + b\n",
        test_status="OK",
        coverage=88.5,
    )

    assert saved["id"] is not None
    assert saved["functionsCount"] == 1
    assert saved["coverage"] == 88.5

    runs = persistence.list_runs()
    assert runs
    assert runs[0]["id"] == saved["id"]

    fetched = persistence.get_run(saved["id"])
    assert fetched is not None
    assert fetched["language"] == "python"
    assert fetched["testStatus"] == "OK"


def test_get_missing_run_returns_none(tmp_path) -> None:
    _configure(tmp_path)
    assert persistence.get_run(999_999) is None
