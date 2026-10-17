"""Pydantic request models for the AI service."""

from typing import Literal

from pydantic import BaseModel, Field

Language = Literal["auto", "python", "cpp", "gp", "generic"]
Provider = Literal["auto", "bedrock", "local"]


class SourceRequest(BaseModel):
    source: str = Field(min_length=1, max_length=100_000)
    language: Language = "auto"


class TestExecutionRequest(BaseModel):
    test_source: str = Field(min_length=1, max_length=100_000)
    source: str | None = Field(default=None, max_length=100_000)
    language: Language = "auto"


class PipelineRequest(BaseModel):
    source: str = Field(min_length=1, max_length=100_000)
    language: Language = "auto"
    provider: Provider = "auto"
    execute: bool = True
    persist: bool = True
