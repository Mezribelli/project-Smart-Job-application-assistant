"""Provider contract shared by Bedrock and the local baseline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GeneratedSuite:
    """A generated pytest suite plus provenance metadata."""

    test_source: str
    provider: str
    model: str | None = None
    rationale: str = ""
    notes: list[str] = field(default_factory=list)


class TestGenerationProvider:
    """Base class for unit-test generation providers."""

    name: str = "base"

    def available(self) -> bool:
        return False

    def describe(self) -> dict[str, Any]:
        return {"provider": self.name, "available": self.available(), "model": None}

    def generate(self, source: str, analysis: dict[str, Any], language: str) -> GeneratedSuite:
        raise NotImplementedError
