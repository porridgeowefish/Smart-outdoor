from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ContextExtractionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    existing_context_state: dict = Field(default_factory=dict)
    content: str = Field(min_length=1)


class ContextExtractionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    context_state: dict
    context_summary: str
    confidence: float = Field(ge=0, le=1)


class ResponseGenerationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["waiting_user", "recommendation", "candidate_detail_card"]
    context_state: dict = Field(default_factory=dict)
    candidate_count: int = Field(default=0, ge=0)
    candidate_routes: list[dict] = Field(default_factory=list)


class ResponseGenerationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    content: str
