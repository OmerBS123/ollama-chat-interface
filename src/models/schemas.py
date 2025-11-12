"""
Data models for type safety and validation.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Chat message model."""

    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ModelInfo(BaseModel):
    """Model information."""

    name: str
    size: int | None = None
    modified_at: datetime | None = None
    digest: str | None = None
    family: str | None = None


class ModelParameters(BaseModel):
    """Model generation parameters."""

    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    max_tokens: int | None = Field(default=None, ge=1)


class ChatSession(BaseModel):
    """Saved chat session."""

    session_id: str
    model_name: str
    messages: list[ChatMessage]
    parameters: ModelParameters
    system_prompt: str | None = None
    created_at: datetime
    updated_at: datetime
