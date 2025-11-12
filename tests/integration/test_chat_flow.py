"""
Integration tests for the chatbot application.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.models.schemas import ModelParameters
from src.services.ollama_service import chat_stream, list_local_models


@pytest.mark.asyncio
async def test_end_to_end_chat_flow() -> None:
    """Test complete chat flow from model listing to response."""
    # Mock ollama responses
    mock_list = MagicMock(
        return_value={
            "models": [
                {
                    "name": "llama3",
                    "size": 1000000,
                    "modified_at": "2024-01-01T00:00:00Z",
                    "digest": "abc123",
                    "details": {"family": "llama"},
                }
            ]
        }
    )

    mock_chat = MagicMock(
        return_value=[
            {"message": {"content": "Hello"}},
            {"message": {"content": " there"}},
        ]
    )

    with patch("src.services.ollama_service.ollama.list", mock_list):
        with patch("src.services.ollama_service.ollama.chat", mock_chat):
            # 1. List models
            models = list_local_models()
            assert len(models) == 1
            assert models[0].name == "llama3"

            # 2. Chat with model
            messages = [{"role": "user", "content": "Hi"}]
            params = ModelParameters()

            response_chunks = []
            async for chunk in chat_stream(messages, "llama3", params):
                response_chunks.append(chunk)

            assert response_chunks == ["Hello", " there"]


def test_model_parameter_validation() -> None:
    """Test model parameters are properly validated."""
    # Valid parameters
    params = ModelParameters(temperature=0.5, top_p=0.8, max_tokens=100)
    assert params.temperature == 0.5
    assert params.top_p == 0.8
    assert params.max_tokens == 100

    # Invalid temperature (too high)
    with pytest.raises(Exception):  # Pydantic validation error
        ModelParameters(temperature=3.0)

    # Invalid top_p (too high)
    with pytest.raises(Exception):
        ModelParameters(top_p=1.5)

    # Invalid max_tokens (negative)
    with pytest.raises(Exception):
        ModelParameters(max_tokens=-1)
