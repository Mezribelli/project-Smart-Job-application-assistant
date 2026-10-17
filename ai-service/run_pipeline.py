"""Command-line entry point for the automated unit-test pipeline.

Usage::

    python run_pipeline.py samples/gp_sample.cpp
    python run_pipeline.py samples/gp_rule_sample.gp --language gp --json
    python run_pipeline.py samples/solution.py --provider bedrock

Exit code is 0 when the generated suite passes (or is skipped) and 1 otherwise,
which makes the script usable directly inside a CI job.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.pipeline import run_pipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the GP unit-test pipeline on a source file.")
    parser.add_argument("source", type=Path, help="Path to the source file to analyse")
    parser.add_argument("--language", default="auto", choices=["auto", "python", "cpp", "gp", "generic"])
    parser.add_argument("--provider", default="auto", choices=["auto", "bedrock", "local"])
    parser.add_argument("--no-execute", action="store_true", help="Only analyse and generate, do not run tests")
    parser.add_argument("--no-persist", action="store_true", help="Do not write the run to the database")
    parser.add_argument("--json", action="store_true", help="Print the full JSON report")
    args = parser.parse_args(argv)

    if not args.source.exists():
        parser.error(f"file not found: {args.source}")

    text = args.source.read_text(encoding="utf-8")
    report = run_pipeline(
        text,
        language=args.language,
        provider=args.provider,
        execute=not args.no_execute,
        persist=not args.no_persist,
    )

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        analysis = report["analysis"]
        execution = report.get("execution")
        print(f"language      : {analysis['language']}")
        print(f"provider      : {report['provider']} (fallback={report['fallback']})")
        print(f"units         : {len(analysis['functions'])} functions, {len(analysis['classes'])} classes")
        print(f"complexity    : {analysis['complexity']}")
        if execution:
            print(f"tests         : {execution['status']} (exit {execution['exitCode']})")
            print(f"coverage      : {execution['coverage']}%")
        print(f"run id        : {report['runId']}")
        print(f"stages        : {', '.join(s['stage'] for s in report['stages'])}")

    execution = report.get("execution")
    if execution is None:
        return 0
    return 0 if execution["status"] == "OK" else 1


if __name__ == "__main__":
    sys.exit(main())
