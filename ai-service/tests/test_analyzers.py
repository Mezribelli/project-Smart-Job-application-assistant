import pytest

from app.analyzers import analyze, detect_language
from app.errors import CodeAnalysisError, UnsupportedLanguageError

PYTHON_SOURCE = "def add(a: int, b: int) -> int:\n    return a + b\n"

CPP_SOURCE = """#include <cmath>
namespace gp {
class Valuation {
public:
    double value(double x) { if (x > 0) { return x; } return 0.0; }
};
}
"""

GP_SOURCE = """INCLUDE common/valuation.gp
RULE ComputeNav(fund_id, valuation_date)
    SELECT sum(market_value) FROM positions WHERE fund = :fund_id;
END
PROCEDURE PostEntry(entry_id)
    INSERT INTO ledger VALUES (:entry_id);
END
"""


def test_detect_python() -> None:
    assert detect_language(PYTHON_SOURCE) == "python"


def test_detect_cpp() -> None:
    assert detect_language(CPP_SOURCE) == "cpp"


def test_detect_gp() -> None:
    assert detect_language(GP_SOURCE) == "gp"


def test_python_analysis() -> None:
    analysis = analyze(PYTHON_SOURCE)

    assert analysis["language"] == "python"
    assert "add" in analysis["functions"]
    assert analysis["details"]["signatures"]["add"]["returns"] == "int"


def test_cpp_analysis() -> None:
    analysis = analyze(CPP_SOURCE)

    assert analysis["language"] == "cpp"
    assert "value" in analysis["functions"]
    assert "Valuation" in analysis["classes"]
    assert "cmath" in analysis["imports"]
    assert analysis["complexity"] >= 2


def test_gp_analysis() -> None:
    analysis = analyze(GP_SOURCE)

    assert analysis["language"] == "gp"
    assert "ComputeNav" in analysis["functions"]
    assert "PostEntry" in analysis["functions"]
    assert "positions" in analysis["details"]["tables"]


def test_explicit_language_overrides_detection() -> None:
    assert analyze(PYTHON_SOURCE, "auto")["language"] == "python"
    assert analyze("x = 1\n", "python")["language"] == "python"


def test_unbalanced_braces_are_rejected() -> None:
    with pytest.raises(CodeAnalysisError):
        analyze("class A { void f() {} ", "cpp")


def test_empty_source_is_rejected() -> None:
    with pytest.raises(CodeAnalysisError):
        analyze("")


def test_unsupported_language_is_rejected() -> None:
    with pytest.raises(UnsupportedLanguageError):
        analyze("x = 1", "cobol")
