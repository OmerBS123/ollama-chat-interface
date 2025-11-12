"""
Pytest configuration and fixtures.
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from src.models.schemas import ChatMessage, ModelInfo, ModelParameters


@pytest.fixture
def mock_ollama_list() -> MagicMock:
    """Mock ollama.list() response."""
    return MagicMock(
        return_value={
            "models": [
                {
                    "name": "llama3",
                    "size": 1000000,
                    "modified_at": "2024-01-01T00:00:00Z",
                    "digest": "abc123",
                    "details": {"family": "llama"},
                },
                {
                    "name": "mistral",
                    "size": 2000000,
                    "modified_at": "2024-01-02T00:00:00Z",
                    "digest": "def456",
                    "details": {"family": "mistral"},
                },
            ]
        }
    )


@pytest.fixture
def mock_ollama_chat() -> MagicMock:
    """Mock ollama.chat() streaming response."""
    return MagicMock(
        return_value=[
            {"message": {"content": "Hello"}},
            {"message": {"content": " world"}},
            {"message": {"content": "!"}},
        ]
    )


@pytest.fixture
def sample_model_info() -> ModelInfo:
    """Sample ModelInfo object."""
    return ModelInfo(
        name="llama3",
        size=1000000,
        modified_at="2024-01-01T00:00:00Z",
        digest="abc123",
        family="llama",
    )


@pytest.fixture
def sample_model_parameters() -> ModelParameters:
    """Sample ModelParameters object."""
    return ModelParameters(temperature=0.7, top_p=0.9, max_tokens=1000)


@pytest.fixture
def sample_chat_messages() -> list[ChatMessage]:
    """Sample chat messages."""
    return [
        ChatMessage(role="user", content="Hello", timestamp=datetime.now()),
        ChatMessage(role="assistant", content="Hi there!", timestamp=datetime.now()),
    ]
