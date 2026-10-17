"""Multi-language analysis entry point.

``analyze`` dispatches to the right analyzer (explicit language or auto-detected)
and always returns the same JSON-serialisable structure::

    {
      "language": "python" | "cpp" | "gp" | "generic",
      "lines": int,
      "functions": [str, ...],
      "classes": [str, ...],
      "imports": [str, ...],
      "complexity": int,
      "details": {...}
    }
"""

from __future__ import annotations

from typing import Any

from ..errors import CodeAnalysisError, UnsupportedLanguageError
from . import cpp_analyzer, gp_analyzer, python_analyzer
from .detector import SUPPORTED_LANGUAGES, detect_language

__all__ = ["analyze", "detect_language", "SUPPORTED_LANGUAGES"]


def _generic_analyze(source: str) -> dict[str, Any]:
    """Fallback for unrecognised languages: brace-aware best effort."""

    if not source.strip():
        raise CodeAnalysisError("Source code must not be empty")
    if "{" in source and "}" in source:
        result = cpp_analyzer.analyze_source(source)
        result["language"] = "generic"
        result["details"]["note"] = "Unrecognised language; brace-based structural extraction applied."
        return result
    return {
        "language": "generic",
        "lines": len(source.splitlines()),
        "functions": [],
        "classes": [],
        "imports": [],
        "complexity": 1,
        "details": {"note": "Unrecognised language; no structural units detected."},
    }


def analyze(source: str, language: str = "auto") -> dict[str, Any]:
    """Analyze ``source`` using the requested (or detected) language."""

    if language not in SUPPORTED_LANGUAGES:
        raise UnsupportedLanguageError(f"Unsupported language: {language}")

    resolved = detect_language(source) if language == "auto" else language
    if resolved == "python":
        return python_analyzer.analyze_source(source)
    if resolved == "cpp":
        return cpp_analyzer.analyze_source(source)
    if resolved == "gp":
        return gp_analyzer.analyze_source(source)
    return _generic_analyze(source)
