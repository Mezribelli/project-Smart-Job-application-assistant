from app.generator import generate_suite

PYTHON_SOURCE = "def add(a: int, b: int) -> int:\n    return a + b\n"
CPP_SOURCE = "#include <cmath>\nnamespace gp {\nclass A {\npublic:\n    double f(double x) { if (x > 0) { return x; } return 0.0; }\n};\n}\n"
GP_SOURCE = "RULE ComputeNav(fund_id)\n    SELECT sum(v) FROM positions;\nEND\n"


def _assert_valid(test_source: str) -> None:
    compile(test_source, "<generated>", "exec")


def test_generate_python_locally() -> None:
    result = generate_suite(PYTHON_SOURCE, provider="local")

    assert result["analysis"]["language"] == "python"
    assert result["provider"] == "local"
    assert result["model"] is None
    assert "def test_add_is_callable" in result["testSource"]
    _assert_valid(result["testSource"])


def test_generate_cpp_produces_contract_tests() -> None:
    result = generate_suite(CPP_SOURCE, provider="local")

    assert result["analysis"]["language"] == "cpp"
    assert "SPEC" in result["testSource"]
    assert "test_expected_units_are_present" in result["testSource"]
    _assert_valid(result["testSource"])


def test_generate_gp_produces_contract_tests() -> None:
    result = generate_suite(GP_SOURCE, provider="local")

    assert result["analysis"]["language"] == "gp"
    assert "test_ComputeNav" in result["testSource"]
    _assert_valid(result["testSource"])


def test_auto_provider_uses_local_when_bedrock_disabled() -> None:
    result = generate_suite(PYTHON_SOURCE, provider="auto")

    assert result["provider"] == "local"
    assert result["fallback"] is False
