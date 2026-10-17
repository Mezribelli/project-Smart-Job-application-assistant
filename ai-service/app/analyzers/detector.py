"""Language detection for the GP code-analysis agent."""

from __future__ import annotations

import re

_PY_SIGNAL = re.compile(r"^\s*(def|class|import|from|async\s+def)\s", re.MULTILINE)
_CPP_INCLUDE = re.compile(r"#\s*include\s*[<\"]")
_CPP_KEYWORDS = re.compile(r"\b(namespace|template|std::|public:|private:|protected:|virtual|#define)\b")
_CPP_TYPES = re.compile(r"\b(class|struct)\s+[A-Za-z_]\w*\s*\{")
_GP_RULE = re.compile(r"^\s*RULE\s+[A-Za-z_]", re.IGNORECASE | re.MULTILINE)
_GP_UNIT = re.compile(r"^\s*(PROCEDURE|PROC|FUNCTION|SUB)\s+[A-Za-z_]", re.IGNORECASE | re.MULTILINE)
_GP_SQL = re.compile(r"\b(SELECT|INSERT\s+INTO|UPDATE|DELETE\s+FROM)\b", re.IGNORECASE)

SUPPORTED_LANGUAGES = ("auto", "python", "cpp", "gp", "generic")


def detect_language(source: str) -> str:
    """Best-effort language detection. Returns one of the supported ids."""

    if not source or not source.strip():
        return "generic"

    if _GP_RULE.search(source):
        return "gp"
    if _GP_UNIT.search(source) and _GP_SQL.search(source):
        return "gp"
    # Python is validated with the real parser before C-inspired heuristics, so
    # that ``class Foo:`` (Python) is never mistaken for ``class Foo {`` (C++).
    if _PY_SIGNAL.search(source):
        import ast

        try:
            ast.parse(source)
            return "python"
        except SyntaxError:
            pass
    if _CPP_INCLUDE.search(source) or _CPP_KEYWORDS.search(source) or _CPP_TYPES.search(source):
        return "cpp"
    if "{" in source and "}" in source and ";" in source:
        return "cpp"
    # A Python signal that failed to parse and did not look like C++ is still
    # treated as Python so the analyzer can raise a precise syntax error.
    if _PY_SIGNAL.search(source):
        return "python"
    return "generic"
