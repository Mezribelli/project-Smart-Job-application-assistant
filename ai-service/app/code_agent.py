"""Backwards-compatible facade over the modular code-analysis agent.

Earlier revisions exposed ``analyze_source`` / ``generate_tests`` /
``execute_tests`` directly from this module. Those names are kept so existing
callers keep working, but they now delegate to the language-aware analyzers,
the provider-based generator and the coverage-aware executor.
"""

from __future__ import annotations

from typing import Any

from .analyzers import python_analyzer
from .executor import execute_test_source
from .generator import generate_suite

__all__ = ["analyze_source", "generate_tests", "execute_tests", "CodeAnalysisError"]

from .errors import CodeAnalysisError  # noqa: E402  (re-exported)


def analyze_source(source: str) -> dict[str, Any]:
    """Analyze Python source (legacy Python-only entry point)."""

    return python_analyzer.analyze_source(source)


def generate_tests(source: str) -> tuple[dict[str, Any], str]:
    """Generate a baseline pytest suite. Returns ``(analysis, test_source)``."""

    result = generate_suite(source, language="python", provider="local")
    return result["analysis"], result["testSource"]


def execute_tests(test_source: str) -> dict[str, Any]:
    """Execute a test suite and return ``{status, exitCode, output, ...}``."""

    return execute_test_source(test_source)
