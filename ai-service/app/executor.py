"""Unit-test execution with optional coverage measurement.

Runs a generated pytest suite in an isolated temporary directory with a hard
timeout and reports an explicit ``OK``/``KO`` verdict, matching the subject's
"execute the unit tests manually and see the result (OK, KO)" requirement.

When the original *Python* solution is supplied it is written next to the tests
as ``solution.py`` and pytest-cov measures line coverage of that file.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from .errors import CodeAnalysisError

OUTPUT_LIMIT = 10_000
DEFAULT_TIMEOUT = 20

_HAS_COVERAGE = importlib.util.find_spec("coverage") is not None


def execute_test_source(
    test_source: str,
    solution_source: str | None = None,
    language: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    if not test_source or not test_source.strip():
        raise CodeAnalysisError("Generated test code must not be empty")
    if len(test_source) > 100_000:
        raise CodeAnalysisError("Test code exceeds the 100000 character limit")

    measure_coverage = bool(solution_source) and (language in (None, "python")) and _HAS_COVERAGE
    with tempfile.TemporaryDirectory(prefix="smart-job-tests-") as directory:
        root = Path(directory)
        (root / "test_generated.py").write_text(test_source, encoding="utf-8")
        (root / "conftest.py").write_text("import sys\nsys.path.insert(0, '.')\n", encoding="utf-8")
        if measure_coverage and solution_source is not None:
            (root / "solution.py").write_text(solution_source, encoding="utf-8")

        pytest_args = ["-m", "pytest", "test_generated.py", "-q", "-p", "no:cacheprovider"]
        if measure_coverage:
            args = [sys.executable, "-m", "coverage", "run", "--include=*solution.py", *pytest_args]
        else:
            args = [sys.executable, *pytest_args]

        try:
            result = subprocess.run(
                args,
                cwd=directory,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise CodeAnalysisError(f"Test execution exceeded {timeout} seconds") from error

        coverage = None
        if measure_coverage:
            coverage = _collect_coverage(directory)

        output = (result.stdout + result.stderr)[-OUTPUT_LIMIT:]

    return {
        "status": "OK" if result.returncode == 0 else "KO",
        "exitCode": result.returncode,
        "output": output,
        "coverage": coverage,
        "coverageAvailable": measure_coverage,
        "tests": _parse_counts(output),
    }


def _collect_coverage(directory: str) -> float | None:
    try:
        subprocess.run(
            [sys.executable, "-m", "coverage", "json", "-o", "coverage.json", "--include=*solution.py"],
            cwd=directory,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except subprocess.TimeoutExpired:  # pragma: no cover - defensive
        return None
    return _read_coverage(Path(directory))


def _read_coverage(root: Path) -> float | None:
    report = root / "coverage.json"
    if not report.exists():
        return None
    try:
        data = json.loads(report.read_text(encoding="utf-8"))
        return round(float(data["totals"]["percent_covered"]), 2)
    except Exception:  # pragma: no cover - defensive
        return None


def _parse_counts(output: str) -> dict[str, int]:
    counts = {"passed": 0, "failed": 0, "skipped": 0}
    for line in output.splitlines():
        stripped = line.strip()
        for key in counts:
            marker = f" {key}"
            if marker in f" {stripped}" and ("=" in stripped or "passed" in stripped or "failed" in stripped or "skipped" in stripped):
                import re

                match = re.search(rf"(\d+) {key}", stripped)
                if match:
                    counts[key] = max(counts[key], int(match.group(1)))
    return counts
