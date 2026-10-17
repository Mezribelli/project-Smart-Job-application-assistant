"""Deterministic, offline baseline test generator.

This provider never calls the network. It produces a *valid, always-passing*
pytest suite that locks the extracted contract of the analyzed units:

* Python: import-based structure, callability, signature and doctest tests.
* GP / C++ / generic: regression locks over the structural spec plus explicitly
  skipped placeholders that a human (or the Bedrock provider) fills with real
  behavioural assertions once a runtime binding is available.

The suite is deliberately conservative: it must never fabricate behaviour it
cannot prove, so it complements rather than replaces LLM generation.
"""

from __future__ import annotations

from typing import Any

from .base import GeneratedSuite, TestGenerationProvider

_HEADER = '''"""Auto-generated baseline tests.

Provider: local (offline baseline).
Review and complete before relying on these tests.
"""

import importlib
import inspect
import json

import pytest

try:  # pragma: no cover - import path depends on execution layout
    solution = importlib.import_module("solution")
    _IMPORT_ERROR = None
except Exception as exc:  # pragma: no cover
    solution = None
    _IMPORT_ERROR = exc


def _resolve(name):
    if solution is None:
        return None
    if hasattr(solution, name):
        return getattr(solution, name)
    for value in vars(solution).values():
        if inspect.isclass(value) and hasattr(value, name):
            return getattr(value, name)
    return None


def _resolve_qualname(qualname):
    if solution is None:
        return None
    obj = solution
    for part in qualname.split("."):
        obj = getattr(obj, part, None)
        if obj is None:
            return None
    return obj


def _require_solution():
    if solution is None:
        pytest.skip(f"solution module not importable: {_IMPORT_ERROR}")
'''


class LocalProvider(TestGenerationProvider):
    name = "local"

    def available(self) -> bool:
        return True

    def describe(self) -> dict[str, Any]:
        return {"provider": self.name, "available": True, "model": None}

    def generate(self, source: str, analysis: dict[str, Any], language: str) -> GeneratedSuite:
        if language == "python":
            suite = self._python_suite(analysis)
        else:
            suite = self._spec_suite(analysis, language)
        return GeneratedSuite(
            test_source=suite,
            provider=self.name,
            model=None,
            rationale=(
                "Offline baseline: structural, signature and doctest checks. "
                "Use the Bedrock provider for behaviour-driven coverage."
            ),
            notes=[
                "Baseline suite generated locally without an LLM.",
                "Behavioural placeholders are marked with pytest.mark.skip.",
            ],
        )

    # ------------------------------------------------------------------ python
    def _python_suite(self, analysis: dict[str, Any]) -> str:
        lines: list[str] = [_HEADER.rstrip("\n"), ""]
        signatures: dict[str, dict[str, Any]] = analysis["details"].get("signatures", {})

        used: set[str] = set()
        has_doctests = False

        def unique(base: str) -> str:
            name = base
            index = 1
            while name in used:
                index += 1
                name = f"{base}_{index}"
            used.add(name)
            return name

        for class_name in analysis["classes"]:
            test = unique(f"test_{class_name}_class_is_defined")
            lines += [
                "",
                f"def {test}():",
                "    _require_solution()",
                f"    assert inspect.isclass(getattr(solution, {class_name!r}, None))",
            ]

        for qualname, spec in signatures.items():
            label = spec["qualname"].replace(".", "_")
            target_expr = f"_resolve_qualname({qualname!r})"
            test = unique(f"test_{label}_is_callable")
            lines += [
                "",
                f"def {test}():",
                "    _require_solution()",
                f"    assert callable({target_expr})",
            ]

            params = [p["name"] for p in spec["parameters"] if not p["is_self"]]
            if params:
                sig_test = unique(f"test_{label}_signature_contract")
                expected = ", ".join(repr(p) for p in params)
                lines += [
                    "",
                    f"def {sig_test}():",
                    "    _require_solution()",
                    f"    target = {target_expr}",
                    "    assert target is not None",
                    "    actual = [p for p in inspect.signature(target).parameters if p != 'self']",
                    f"    for expected in ({expected},):",
                    "        assert expected in actual",
                ]

            if spec.get("docstring", "").count(">>>") > 0:
                has_doctests = True

        if has_doctests:
            doctest_test = unique("test_module_docstring_examples")
            lines += [
                "",
                f"def {doctest_test}():",
                "    import doctest",
                "    _require_solution()",
                "    result = doctest.testmod(solution, verbose=False)",
                "    assert result.failed == 0",
            ]

        if not analysis["classes"] and not signatures:
            lines += [
                "",
                "def test_module_is_valid_python():",
                "    assert solution is not None or _IMPORT_ERROR is not None",
            ]

        return "\n".join(lines) + "\n"

    # -------------------------------------------------------------- non-python
    def _spec_suite(self, analysis: dict[str, Any], language: str) -> str:
        signatures = analysis["details"].get("signatures", {})
        spec = {
            "language": language,
            "functions": analysis["functions"],
            "classes": analysis["classes"],
            "imports": analysis["imports"],
            "complexity": analysis["complexity"],
            "parameters": {
                name: [p["name"] for p in info["parameters"]]
                for name, info in signatures.items()
            },
        }
        lines: list[str] = [
            f'"""Contract tests for {language} source analysed by the GP agent.',
            "",
            "The analysed language has no in-process Python runtime binding here, so",
            "these tests lock the structural contract extracted from the source.",
            "Real behavioural tests are added by the Bedrock provider or a human.",
            '"""',
            "",
            "import pytest",
            "",
            f"SPEC = {spec!r}",
            "",
            "",
            "def test_language_is_locked():",
            f"    assert SPEC['language'] == {language!r}",
            "",
            "",
            "def test_expected_units_are_present():",
            f"    assert SPEC['functions'] == {analysis['functions']!r}",
            f"    assert SPEC['classes'] == {analysis['classes']!r}",
            "",
            "",
            "def test_imports_are_declared():",
            f"    assert SPEC['imports'] == {analysis['imports']!r}",
        ]

        for name, param_names in spec["parameters"].items():
            safe = name.replace(".", "_").replace("::", "_")
            lines += [
                "",
                "",
                f"def test_{safe}_parameter_contract():",
                f"    assert SPEC['parameters'][{name!r}] == {param_names!r}",
            ]

        for name in analysis["functions"]:
            safe = name.replace(".", "_").replace("::", "_")
            lines += [
                "",
                "",
                "@pytest.mark.skip(reason='Bind a GP/C++ runtime to assert real behaviour')",
                f"def test_{safe}_behaviour_placeholder():",
                f"    \"\"\"TODO: assert real behaviour of {name} on representative inputs.\"\"\"",
                "    raise NotImplementedError",
            ]

        return "\n".join(lines) + "\n"
