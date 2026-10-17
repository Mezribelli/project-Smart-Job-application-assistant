from app.code_agent import analyze_source, execute_tests, generate_tests


def test_analyze_source_finds_functions_and_imports() -> None:
    result = analyze_source("import math\n\ndef add(left, right):\n    return left + right\n")

    assert result["functions"] == ["add"]
    assert result["imports"] == ["math"]


def test_generate_tests_returns_executable_baseline() -> None:
    analysis, tests = generate_tests("def add(left, right):\n    return left + right\n")

    assert analysis["functions"] == ["add"]
    assert "test_add_is_callable" in tests
    result = execute_tests(tests)
    assert result["status"] == "OK"


def test_generate_tests_with_class_and_methods() -> None:
    source = "class Calculator:\n    def multiply(self, a, b):\n        return a * b\n"
    analysis, tests = generate_tests(source)

    assert "Calculator" in analysis["classes"]
    assert "multiply" in analysis["functions"]
    assert "test_Calculator_class_is_defined" in tests
    assert "test_Calculator_multiply_is_callable" in tests
    result = execute_tests(tests)
    assert result["status"] == "OK"


def test_invalid_python_is_rejected() -> None:
    try:
        analyze_source("def broken(:")
    except ValueError as error:
        assert "Invalid Python syntax" in str(error)
    else:
        raise AssertionError("Invalid source should be rejected")
