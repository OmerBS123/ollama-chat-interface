"""
Tests for ollama_service module.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.models.schemas import ModelInfo, ModelParameters
from src.services.ollama_service import (
    OllamaNotRunningError,
    chat_stream,
    delete_model,
    list_local_models,
    pull_model,
)


def test_list_local_models_success(mock_ollama_list: MagicMock) -> None:
    """Test listing local models returns ModelInfo objects."""
    with patch("src.services.ollama_service.ollama.list", mock_ollama_list):
        models = list_local_models()

        assert len(models) == 2
        assert isinstance(models[0], ModelInfo)
        assert models[0].name == "llama3"
        assert models[0].family == "llama"
        assert models[1].name == "mistral"
        assert models[1].family == "mistral"


def test_list_local_models_connection_error() -> None:
    """Test list_local_models raises OllamaNotRunningError on connection failure."""
    with patch("src.services.ollama_service.ollama.list", side_effect=ConnectionError()):
        with pytest.raises(OllamaNotRunningError):
            list_local_models()


@pytest.mark.asyncio
async def test_chat_stream_success(mock_ollama_chat: MagicMock) -> None:
    """Test streaming chat returns content chunks."""
    with patch("src.services.ollama_service.ollama.chat", mock_ollama_chat):
        messages = [{"role": "user", "content": "Hi"}]
        params = ModelParameters()

        chunks = []
        async for chunk in chat_stream(messages, "llama3", params):
            chunks.append(chunk)

        assert chunks == ["Hello", " world", "!"]


@pytest.mark.asyncio
async def test_chat_stream_with_max_tokens(mock_ollama_chat: MagicMock) -> None:
    """Test chat_stream passes num_predict when max_tokens is set."""
    with patch("src.services.ollama_service.ollama.chat", mock_ollama_chat) as mock:
        messages = [{"role": "user", "content": "Hi"}]
        params = ModelParameters(max_tokens=100)

        chunks = []
        async for chunk in chat_stream(messages, "llama3", params):
            chunks.append(chunk)

        # Verify num_predict was passed in options
        call_args = mock.call_args
        assert call_args[1]["options"]["num_predict"] == 100


@pytest.mark.asyncio
async def test_chat_stream_connection_error() -> None:
    """Test chat_stream raises OllamaNotRunningError on connection failure."""
    with patch("src.services.ollama_service.ollama.chat", side_effect=ConnectionError()):
        messages = [{"role": "user", "content": "Hi"}]
        params = ModelParameters()

        with pytest.raises(OllamaNotRunningError):
            async for _ in chat_stream(messages, "llama3", params):
                pass


@pytest.mark.asyncio
async def test_pull_model_success() -> None:
    """Test pulling a model works asynchronously."""
    with patch("src.services.ollama_service.ollama.pull") as mock_pull:
        await pull_model("llama3")
        mock_pull.assert_called_once_with("llama3")


@pytest.mark.asyncio
async def test_pull_model_connection_error() -> None:
    """Test pull_model raises OllamaNotRunningError on connection failure."""
    with patch("src.services.ollama_service.ollama.pull", side_effect=ConnectionError()):
        with pytest.raises(OllamaNotRunningError):
            await pull_model("llama3")


def test_delete_model_success() -> None:
    """Test deleting a model calls correct API."""
    with patch("src.services.ollama_service.ollama.delete") as mock_delete:
        delete_model("llama3")
        mock_delete.assert_called_once_with("llama3")


def test_delete_model_connection_error() -> None:
    """Test delete_model raises OllamaNotRunningError on connection failure."""
    with patch("src.services.ollama_service.ollama.delete", side_effect=ConnectionError()):
        with pytest.raises(OllamaNotRunningError):
            delete_model("llama3")
