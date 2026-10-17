"""Python source analyzer built on the standard :mod:`ast` module.

It extracts structure (functions, classes, imports), per-function signatures
and a lightweight cyclomatic-complexity estimate. The extra signature metadata
is what lets the generator emit *behavioural* pytest cases instead of only
"is defined" smoke checks.
"""

from __future__ import annotations

import ast
from typing import Any

from ..errors import CodeAnalysisError

MAX_SOURCE_CHARS = 100_000
MAX_LINES = 20_000


def _complexity_of(node: ast.AST) -> int:
    score = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler,
                              ast.With, ast.AsyncWith, ast.IfExp, ast.comprehension)):
            score += 1
        elif isinstance(child, ast.BoolOp):
            score += len(child.values) - 1
    return score


def _annotation(node: ast.AST | None) -> str | None:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:  # pragma: no cover - defensive
        return None


def _argument_spec(arg: ast.arg, default: ast.AST | None = None) -> dict[str, Any]:
    return {
        "name": arg.arg,
        "annotation": _annotation(arg.annotation),
        "default": _annotation(default) if default is not None else None,
        "is_self": arg.arg in {"self", "cls"},
    }


def _signature(node: ast.FunctionDef | ast.AsyncFunctionDef, qualname: str) -> dict[str, Any]:
    args = node.args
    positional = list(args.posonlyargs) + list(args.args)
    defaults: list[ast.AST | None] = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
    parameters = [
        _argument_spec(arg, default) for arg, default in zip(positional, defaults)
    ]
    parameters += [_argument_spec(arg) for arg in args.kwonlyargs]

    returns: list[str] = []
    for stmt in ast.walk(node):
        if isinstance(stmt, ast.Return) and stmt.value is not None:
            returns.append(_annotation(stmt.value) or "expr")

    raises: list[str] = []
    for stmt in ast.walk(node):
        if isinstance(stmt, ast.Raise) and stmt.exc is not None:
            exc = stmt.exc
            if isinstance(exc, ast.Call):
                raises.append(ast.unparse(exc.func))
            else:
                raises.append(ast.unparse(exc))

    return {
        "name": node.name,
        "qualname": qualname,
        "is_method": "." in qualname,
        "is_async": isinstance(node, ast.AsyncFunctionDef),
        "parameters": parameters,
        "returns": _annotation(node.returns),
        "docstring": ast.get_docstring(node) or "",
        "complexity": _complexity_of(node),
        "raises": sorted(set(raises)),
        "return_count": len(returns),
    }


def analyze_source(source: str) -> dict[str, Any]:
    """Analyze Python source and return a JSON-serialisable structure."""

    if not source or not source.strip():
        raise CodeAnalysisError("Source code must not be empty")
    if len(source) > MAX_SOURCE_CHARS:
        raise CodeAnalysisError(f"Source code exceeds the {MAX_SOURCE_CHARS} character limit")
    if len(source.splitlines()) > MAX_LINES:
        raise CodeAnalysisError(f"Source code exceeds the {MAX_LINES} line limit")
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        raise CodeAnalysisError(f"Invalid Python syntax: {error.msg}") from error

    functions: list[str] = []
    classes: list[str] = []
    imports: list[str] = []
    signatures: dict[str, dict[str, Any]] = {}

    def visit_body(body: list[ast.stmt], class_stack: list[str]) -> None:
        for node in body:
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
                class_stack.append(node.name)
                visit_body(node.body, class_stack)
                class_stack.pop()
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qualname = ".".join(class_stack + [node.name])
                functions.append(node.name)
                signatures[qualname] = _signature(node, qualname)

    visit_body(tree.body, [])

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")

    total_complexity = sum(spec["complexity"] for spec in signatures.values()) or 1

    return {
        "language": "python",
        "lines": len(source.splitlines()),
        "functions": functions,
        "classes": classes,
        "imports": sorted(set(filter(None, imports))),
        "complexity": total_complexity,
        "details": {
            "signatures": signatures,
            "async_functions": sorted(
                name for name, spec in signatures.items() if spec["is_async"]
            ),
        },
    }
