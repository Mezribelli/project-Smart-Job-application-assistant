"""Structural analyzer for C/C++ source, the primary development language of
NeoXam GP back-office components (GP3/GP4 are C/C++-centric).

This is a *heuristic* analyzer: it does not compile the code. It extracts the
pieces the test generator needs (functions, methods, classes/structs, includes
and a complexity estimate) using carefully ordered regular expressions, then
normalises them into the same JSON contract as the Python analyzer.
"""

from __future__ import annotations

import re
from typing import Any

from ..errors import CodeAnalysisError

MAX_SOURCE_CHARS = 100_000

_COMMENT_BLOCK = re.compile(r"/\*.*?\*/", re.DOTALL)
_COMMENT_LINE = re.compile(r"//[^\n]*")

_INCLUDE = re.compile(r'#\s*include\s*[<"]([^>"]+)[>"]')
_NAMESPACE = re.compile(r"\bnamespace\s+([A-Za-z_]\w*)")
_TYPE_DECL = re.compile(r"\b(?:class|struct|union|enum(?:\s+class)?)\s+([A-Za-z_]\w*)")
_FUNCTION = re.compile(
    r"(?P<ret>(?:[A-Za-z_][\w:<>,\s*&~]*?))\s+"
    r"(?P<name>[A-Za-z_]\w*(?:::[A-Za-z_]\w*)?)\s*"
    r"\((?P<args>[^;{}()]*)\)\s*"
    r"(?:const\s*)?(?:noexcept\s*)?(?:override\s*)?"
    r"(?P<body>\{)",
    re.MULTILINE,
)
_KEYWORDS = {
    "if", "for", "while", "switch", "return", "sizeof", "catch", "case",
    "typedef", "define", "include", "namespace", "class", "struct", "using",
}
_BRANCH = re.compile(r"\b(if|for|while|case|catch|else\s+if)\b|\&\&|\|\||\?")
_FIELD = re.compile(r"^\s*(?:[A-Za-z_][\w:<>,\s*&]*?)\s+([A-Za-z_]\w*)\s*(?:=\s*[^;]+)?;", re.MULTILINE)


def _strip_comments(source: str) -> str:
    return _COMMENT_LINE.sub("", _COMMENT_BLOCK.sub("", source))


def _split_args(raw: str) -> list[dict[str, Any]]:
    args: list[dict[str, Any]] = []
    depth = 0
    current = ""
    for char in raw:
        if char in "<([{":
            depth += 1
        elif char in ">)]}":
            depth -= 1
        if char == "," and depth == 0:
            args.append(current)
            current = ""
        else:
            current += char
    if current.strip():
        args.append(current)

    parsed: list[dict[str, Any]] = []
    for index, arg in enumerate(args):
        cleaned = arg.strip()
        if cleaned in {"", "void"}:
            continue
        tokens = cleaned.replace("&", " ").replace("*", " ").split()
        name = None
        if len(tokens) >= 2 and re.fullmatch(r"[A-Za-z_]\w*", tokens[-1]):
            name = tokens[-1]
            annotation = " ".join(tokens[:-1]).strip() or None
        else:
            annotation = cleaned or None
        parsed.append(
            {
                "name": name or f"arg{index}",
                "annotation": annotation,
                "default": None,
                "is_self": False,
            }
        )
    return parsed


def analyze_source(source: str) -> dict[str, Any]:
    if not source or not source.strip():
        raise CodeAnalysisError("Source code must not be empty")
    if len(source) > MAX_SOURCE_CHARS:
        raise CodeAnalysisError(f"Source code exceeds the {MAX_SOURCE_CHARS} character limit")

    if source.count("{") != source.count("}"):
        raise CodeAnalysisError("Unbalanced braces: source is not valid C/C++")

    code = _strip_comments(source)

    includes = sorted({match for match in _INCLUDE.findall(code)})
    namespaces = _NAMESPACE.findall(code)
    types = _TYPE_DECL.findall(code)

    functions: list[str] = []
    signatures: dict[str, dict[str, Any]] = {}
    seen: set[str] = set()

    for match in _FUNCTION.finditer(code):
        name = match.group("name")
        if name in _KEYWORDS:
            continue
        ret = match.group("ret").strip()
        if ret.split()[-1] in _KEYWORDS and ret.split()[-1] not in {"const"}:
            continue
        span_start = match.start("body")
        span_end = _match_brace(code, span_start)
        body = code[span_start:span_end]
        if name not in seen:
            functions.append(name)
            seen.add(name)
        signatures[name] = {
            "name": name,
            "qualname": name,
            "is_method": "::" in name,
            "is_async": False,
            "parameters": _split_args(match.group("args")),
            "returns": ret or None,
            "docstring": "",
            "complexity": 1 + len(_BRANCH.findall(body)),
            "raises": [],
            "return_count": body.count("return"),
        }

    complexity = sum(spec["complexity"] for spec in signatures.values()) or 1

    return {
        "language": "cpp",
        "lines": len(source.splitlines()),
        "functions": functions,
        "classes": types,
        "imports": includes,
        "complexity": complexity,
        "details": {
            "signatures": signatures,
            "namespaces": sorted(set(namespaces)),
            "fields": _FIELD.findall(code)[:100],
        },
    }


def _match_brace(code: str, open_index: int) -> int:
    depth = 0
    for index in range(open_index, len(code)):
        if code[index] == "{":
            depth += 1
        elif code[index] == "}":
            depth -= 1
            if depth == 0:
                return index
    return len(code)
