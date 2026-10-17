"""Automated unit-test pipeline.

Orchestrates the four subject stages end-to-end:

1. Analyse the GP source (multi-language).
2. Generate a Python pytest suite (Bedrock, else offline baseline).
3. Execute the suite and produce an OK/KO verdict plus coverage.
4. Persist the run to SQL and return a structured report.

This is the same logic exposed by the ``/api/code/pipeline`` endpoint and the
``run_pipeline.py`` CLI, so the automated pipeline and the manual flow share one
implementation.
"""

from __future__ import annotations

import time
from typing import Any

from .executor import execute_test_source
from .generator import generate_suite
from . import persistence


def run_pipeline(
    source: str,
    language: str = "auto",
    provider: str = "auto",
    execute: bool = True,
    persist: bool = True,
) -> dict[str, Any]:
    stages: list[dict[str, Any]] = []

    start = time.perf_counter()
    generated = generate_suite(source, language=language, provider=provider)
    stages.append({"stage": "generate", "durationMs": _ms(start), "provider": generated["provider"]})

    execution: dict[str, Any] | None = None
    if execute:
        start = time.perf_counter()
        execution = execute_test_source(
            generated["testSource"],
            solution_source=source,
            language=generated["analysis"]["language"],
        )
        stages.append(
            {
                "stage": "execute",
                "durationMs": _ms(start),
                "status": execution["status"],
                "coverage": execution["coverage"],
            }
        )

    run_id: int | None = None
    if persist:
        start = time.perf_counter()
        try:
            saved = persistence.save_run(
                language=generated["analysis"]["language"],
                provider=generated["provider"],
                model=generated["model"],
                analysis=generated["analysis"],
                test_source=generated["testSource"],
                source=source,
                test_status=(execution or {}).get("status"),
                coverage=(execution or {}).get("coverage"),
            )
            run_id = saved["id"]
            stages.append({"stage": "persist", "durationMs": _ms(start), "runId": run_id})
        except Exception as error:  # pragma: no cover - persistence must not break the pipeline
            stages.append({"stage": "persist", "durationMs": _ms(start), "error": str(error)})

    return {
        "analysis": generated["analysis"],
        "testSource": generated["testSource"],
        "provider": generated["provider"],
        "model": generated["model"],
        "notes": generated["notes"],
        "rationale": generated["rationale"],
        "fallback": generated["fallback"],
        "execution": execution,
        "runId": run_id,
        "stages": stages,
    }


def _ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)
