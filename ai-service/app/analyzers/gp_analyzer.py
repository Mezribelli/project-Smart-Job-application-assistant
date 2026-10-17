"""Heuristic analyzer for the GP back-office rule/scripting dialect.

NeoXam GP exposes business logic through configurable, rule-driven engines
(Position Keeping, Valuation, Accounting). Custom client logic is expressed in
a SQL-flavoured, rule/script DSL rather than plain C++. Because that dialect is
proprietary, this analyzer recognises the structural constructs that are stable
across GP rule files -- RULE blocks, PROCEDURE/FUNCTION definitions, include
directives, SQL statements and control-flow keywords -- and normalises them into
the shared JSON contract.

The analyzer is intentionally conservative: it never claims to "understand" the
business semantics, it only exposes structure so the generator can propose
Python contract tests around the extracted units.
"""

from __future__ import annotations

import re
from typing import Any

from ..errors import CodeAnalysisError

MAX_SOURCE_CHARS = 100_000

_INCLUDE = re.compile(r"^\s*(?:#?\s*(?:INCLUDE|INCLUDELIB|USING))\s+[\"']?([\w./\\-]+)[\"']?", re.IGNORECASE | re.MULTILINE)
_RULE = re.compile(r"^\s*RULE\s+([A-Za-z_][\w.]*)\s*(?:\(([^)]*)\))?", re.IGNORECASE | re.MULTILINE)
_PROC = re.compile(r"^\s*(?:PROCEDURE|PROC|FUNCTION|SUB|METHOD)\s+([A-Za-z_]\w*)\s*(?:\(([^)]*)\))?", re.IGNORECASE | re.MULTILINE)
_TABLE = re.compile(r"\b(?:FROM|JOIN|UPDATE|INTO)\s+([A-Za-z_][\w.]*)", re.IGNORECASE)
_PARAM = re.compile(r"[@:$]([A-Za-z_]\w*)")
_BRANCH = re.compile(r"\b(IF|ELSE|ELSIF|ELSEIF|CASE|WHILE|FOR|LOOP|AND|OR)\b", re.IGNORECASE)
_STATEMENT = re.compile(r";")


def _params(raw: str | None) -> list[dict[str, Any]]:
    if not raw:
        return []
    parsed: list[dict[str, Any]] = []
    for index, part in enumerate(raw.strip().split(",")):
        cleaned = part.strip()
        if not cleaned:
            continue
        tokens = cleaned.split()
        name = tokens[-1] if len(tokens) == 1 else tokens[0]
        annotation = None if len(tokens) == 1 else " ".join(tokens[1:])
        parsed.append(
            {"name": name, "annotation": annotation, "default": None, "is_self": False}
        )
    return parsed


def analyze_source(source: str) -> dict[str, Any]:
    if not source or not source.strip():
        raise CodeAnalysisError("Source code must not be empty")
    if len(source) > MAX_SOURCE_CHARS:
        raise CodeAnalysisError(f"Source code exceeds the {MAX_SOURCE_CHARS} character limit")

    includes = sorted(set(_INCLUDE.findall(source)))

    rules = _RULE.findall(source)
    procedures = _PROC.findall(source)

    functions: list[str] = []
    signatures: dict[str, dict[str, Any]] = {}
    for name, args in procedures:
        functions.append(name)
        signatures[name] = {
            "name": name,
            "qualname": name,
            "is_method": False,
            "is_async": False,
            "parameters": _params(args),
            "returns": None,
            "docstring": "",
            "complexity": 1,
            "raises": [],
            "return_count": 0,
        }
    for name, args in rules:
        functions.append(name)
        signatures[name] = {
            "name": name,
            "qualname": name,
            "is_method": False,
            "is_async": False,
            "parameters": _params(args),
            "returns": None,
            "docstring": "GP rule unit",
            "complexity": 1,
            "raises": [],
            "return_count": 0,
        }

    tables = sorted({name for name in _TABLE.findall(source)})
    parameters = sorted({name for name in _PARAM.findall(source)})
    complexity = 1 + len(_BRANCH.findall(source))

    for name in signatures:
        block = _extract_block(source, name)
        signatures[name]["complexity"] = 1 + len(_BRANCH.findall(block)) if block else 1

    return {
        "language": "gp",
        "lines": len(source.splitlines()),
        "functions": functions,
        "classes": [name for name, _ in rules],
        "imports": includes,
        "complexity": complexity,
        "details": {
            "signatures": signatures,
            "rules": [name for name, _ in rules],
            "tables": tables,
            "parameters": parameters,
            "statements": len(_STATEMENT.findall(source)),
        },
    }


def _extract_block(source: str, name: str) -> str:
    pattern = re.compile(rf"\b{re.escape(name)}\b(.*?)(?:\bEND\b|$)", re.IGNORECASE | re.DOTALL)
    match = pattern.search(source)
    return match.group(1) if match else ""
