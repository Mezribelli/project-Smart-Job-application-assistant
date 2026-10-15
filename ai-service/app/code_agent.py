import ast
import subprocess
import sys
import tempfile
from pathlib import Path


class CodeAnalysisError(ValueError):
    """Raised when submitted source cannot be analyzed safely."""


def analyze_source(source: str) -> dict[str, object]:
    if not source.strip():
        raise CodeAnalysisError("Source code must not be empty")
    if len(source) > 100_000:
        raise CodeAnalysisError("Source code exceeds the 100000 character limit")
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        raise CodeAnalysisError(f"Invalid Python syntax: {error.msg}") from error

    functions = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    classes = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
    ]
    imports = [
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    ]
    imports.extend(
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    )
    return {
        "functions": functions,
        "classes": classes,
        "imports": sorted(set(filter(None, imports))),
        "lines": len(source.splitlines()),
    }


def generate_tests(source: str) -> tuple[dict[str, object], str]:
    analysis = analyze_source(source)
    functions = analysis["functions"]
    classes = analysis["classes"]
    test_lines = [
        "import pytest",
        "",
        "# Generated baseline tests. Review and customize before relying on them.",
        "SOURCE = " + repr(source),
        "",
        "def test_source_is_valid_python():",
        "    compile(SOURCE, '<submitted-source>', 'exec')",
    ]
    for cls_name in classes:
        test_lines.extend(
            [
                "",
                f"def test_{cls_name}_class_is_defined():",
                f"    namespace = {{}}",
                "    exec(compile(SOURCE, '<submitted-source>', 'exec'), namespace)",
                f"    assert isinstance(namespace.get({cls_name!r}), type)",
            ]
        )
    for name in functions:
        test_lines.extend(
            [
                "",
                f"def test_{name}_is_defined():",
                f"    namespace = {{}}",
                "    exec(compile(SOURCE, '<submitted-source>', 'exec'), namespace)",
                f"    target = namespace.get({name!r})",
                "    if target is None:",
                "        for obj in namespace.values():",
                f"            if isinstance(obj, type) and hasattr(obj, {name!r}):",
                f"                target = getattr(obj, {name!r})",
                "                break",
                "    assert callable(target)",
            ]
        )
    if not functions and not classes:
        test_lines.extend(
            [
                "",
                "def test_module_has_no_testable_functions():",
                "    assert isinstance(SOURCE, str)",
            ]
        )
    return analysis, "\n".join(test_lines) + "\n"


def execute_tests(test_source: str) -> dict[str, object]:
    if not test_source.strip():
        raise CodeAnalysisError("Generated test code must not be empty")
    if len(test_source) > 100_000:
        raise CodeAnalysisError("Test code exceeds the 100000 character limit")
    with tempfile.TemporaryDirectory(prefix="smart-job-tests-") as directory:
        test_file = Path(directory) / "test_generated.py"
        test_file.write_text(test_source, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_file), "-q"],
            cwd=directory,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    return {
        "status": "OK" if result.returncode == 0 else "KO",
        "exitCode": result.returncode,
        "output": (result.stdout + result.stderr)[-10_000:],
    }
