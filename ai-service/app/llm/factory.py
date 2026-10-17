"""Provider selection: prefer Bedrock, fall back to the offline baseline."""

from __future__ import annotations

from typing import Any

from .base import TestGenerationProvider
from .bedrock_provider import BedrockProvider
from .local_provider import LocalProvider

PROVIDER_NAMES = ("auto", "bedrock", "local")


def get_provider(name: str = "auto") -> TestGenerationProvider:
    if name == "local":
        return LocalProvider()
    if name == "bedrock":
        return BedrockProvider()
    if name != "auto":
        raise ValueError(f"Unknown provider: {name}")
    bedrock = BedrockProvider()
    return bedrock if bedrock.available() else LocalProvider()


def provider_status() -> list[dict[str, Any]]:
    return [BedrockProvider().describe(), LocalProvider().describe()]
