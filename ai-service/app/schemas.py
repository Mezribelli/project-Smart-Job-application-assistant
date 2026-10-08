from pydantic import BaseModel, Field


class SourceRequest(BaseModel):
    source: str = Field(min_length=1, max_length=100_000)


class TestExecutionRequest(BaseModel):
    test_source: str = Field(min_length=1, max_length=100_000)
