import pytest

from app.errors import CodeAnalysisError
from app.executor import execute_test_source
from app.generator import generate_suite

PYTHON_SOURCE = """def add(a: int, b: int) -> int:
    '''Add two integers.

    >>> add(2, 3)
    5
    '''
    return a + b
"""


def test_execute_generated_suite_ok_with_coverage() -> None:
    suite = generate_suite(PYTHON_SOURCE, provider="local")

    result = execute_test_source(suite["testSource"], solution_source=PYTHON_SOURCE, language="python")

    assert result["status"] == "OK"
    assert result["exitCode"] == 0
    assert result["coverage"] is not None
    assert result["coverage"] > 0


def test_execute_failing_suite_returns_ko() -> None:
    failing = "def test_always_fails():\n    assert 1 == 2\n"

    result = execute_test_source(failing)

    assert result["status"] == "KO"
    assert result["exitCode"] != 0


def test_execute_empty_suite_is_rejected() -> None:
    with pytest.raises(CodeAnalysisError):
        execute_test_source("")


def test_execute_cpp_contract_suite_ok() -> None:
    cpp = "#include <cmath>\nnamespace gp {\ndouble f(double x) { if (x > 0) { return x; } return 0.0; }\n}\n"
    suite = generate_suite(cpp, provider="local")

    result = execute_test_source(suite["testSource"], solution_source=cpp, language="cpp")

    assert result["status"] == "OK"
    assert result["coverage"] is None
