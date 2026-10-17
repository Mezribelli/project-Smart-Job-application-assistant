"""Test-suite generation orchestration.

Analyses the source, selects a provider (Bedrock when configured, otherwise the
offline baseline), validates that the generated Python is syntactically valid,
and transparently falls back to the baseline if the LLM output is unusable.
"""

from __future__ import annotations

from typing import Any

from .analyzers import analyze
from .errors import CodeAnalysisError
from .llm.bedrock_provider import BedrockUnavailable
from .llm.factory import get_provider
from .llm.local_provider import LocalProvider


def _is_valid_python(test_source: str) -> bool:
    if not test_source or not test_source.strip():
        return False
    try:
        compile(test_source, "<generated-tests>", "exec")
    except SyntaxError:
        return False
    return True


def generate_suite(
    source: str,
    language: str = "auto",
    provider: str = "auto",
) -> dict[str, Any]:
    """Generate a pytest suite for ``source``.

    Returns a JSON-serialisable dict with the analysis, the test source and
    provenance metadata (which provider/model produced it, and whether a
    fallback occurred).
    """

    analysis = analyze(source, language)
    resolved_language = analysis["language"]
    notes: list[str] = []
    fallback = False
    rationale = ""
    model: str | None = None

    selected = get_provider(provider)
    try:
        suite = selected.generate(source, analysis, resolved_language)
        model = suite.model
        rationale = suite.rationale
        notes.extend(suite.notes)
        test_source = suite.test_source
        provider_name = suite.provider
    except (BedrockUnavailable, Exception) as error:  # noqa: BLE001 - deliberate fallback
        fallback = True
        notes.append(f"Provider '{selected.name}' unavailable/failed: {error}")
        baseline = LocalProvider().generate(source, analysis, resolved_language)
        test_source = baseline.test_source
        provider_name = baseline.provider
        notes.extend(baseline.notes)

    if not _is_valid_python(test_source):
        fallback = True
        notes.append("Generated suite was not valid Python; using offline baseline.")
        baseline = LocalProvider().generate(source, analysis, resolved_language)
        test_source = baseline.test_source
        provider_name = baseline.provider
        model = None

    if not test_source.endswith("\n"):
        test_source += "\n"

    return {
        "analysis": analysis,
        "testSource": test_source,
        "provider": provider_name,
        "model": model,
        "rationale": rationale,
        "notes": notes,
        "fallback": fallback,
    }


def generate_tests(source: str) -> tuple[dict[str, Any], str]:
    """Backwards-compatible helper returning ``(analysis, test_source)``."""

    result = generate_suite(source, language="python", provider="local")
    return result["analysis"], result["testSource"]
