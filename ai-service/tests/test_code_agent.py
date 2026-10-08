from app.code_agent import analyze_source, generate_tests


def test_analyze_source_finds_functions_and_imports() -> None:
    result = analyze_source("import math\n\ndef add(left, right):\n    return left + right\n")

    assert result["functions"] == ["add"]
    assert result["imports"] == ["math"]


def test_generate_tests_returns_executable_baseline() -> None:
    analysis, tests = generate_tests("def add(left, right):\n    return left + right\n")

    assert analysis["functions"] == ["add"]
    assert "test_add_is_defined" in tests


def test_invalid_python_is_rejected() -> None:
    try:
        analyze_source("def broken(:")
    except ValueError as error:
        assert "Invalid Python syntax" in str(error)
    else:
        raise AssertionError("Invalid source should be rejected")
