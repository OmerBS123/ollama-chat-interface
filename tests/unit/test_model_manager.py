"""
Tests for model_manager module.
"""

from unittest.mock import MagicMock, patch

import requests

from src.models.schemas import ModelInfo
from src.services.model_manager import filter_models, get_available_models, list_cloud_models


def test_list_cloud_models_success() -> None:
    """Test listing cloud models with successful response."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "models": [
            {"name": "gpt-neo"},
            {"name": "gpt-4"},
        ]
    }

    with patch("src.services.model_manager.requests.get", return_value=mock_response):
        models = list_cloud_models()

        assert len(models) == 2
        assert isinstance(models[0], ModelInfo)
        assert models[0].name == "gpt-neo"
        assert models[1].name == "gpt-4"


def test_list_cloud_models_with_api_key() -> None:
    """Test cloud models request includes API key in headers."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"models": []}

    with patch("src.services.model_manager.requests.get", return_value=mock_response) as mock_get:
        with patch("src.services.model_manager.get_settings") as mock_settings:
            mock_settings.return_value.ollama_api_key = "test_key"
            list_cloud_models()

            call_args = mock_get.call_args
            assert call_args[1]["headers"]["Authorization"] == "Bearer test_key"


def test_list_cloud_models_network_error() -> None:
    """Test cloud models returns empty list on network error."""
    with patch(
        "src.services.model_manager.requests.get",
        side_effect=requests.RequestException("Network error"),
    ):
        models = list_cloud_models()
        assert models == []


def test_filter_models_basic() -> None:
    """Test basic regex filtering is case-insensitive."""
    models = [
        ModelInfo(name="GPT-4"),
        ModelInfo(name="llama3"),
        ModelInfo(name="gpt-neo"),
    ]

    filtered = filter_models(models, r"gpt")

    assert len(filtered) == 2
    assert filtered[0].name == "GPT-4"
    assert filtered[1].name == "gpt-neo"


def test_filter_models_regex() -> None:
    """Test advanced regex patterns work."""
    models = [
        ModelInfo(name="llama3"),
        ModelInfo(name="llama2"),
        ModelInfo(name="mistral"),
    ]

    filtered = filter_models(models, r"llama\d")

    assert len(filtered) == 2
    assert all("llama" in m.name for m in filtered)


def test_filter_models_empty_pattern() -> None:
    """Test empty pattern returns all models."""
    models = [
        ModelInfo(name="model1"),
        ModelInfo(name="model2"),
    ]

    filtered = filter_models(models, "")

    assert len(filtered) == 2
    assert filtered == models


def test_filter_models_invalid_regex() -> None:
    """Test invalid regex returns all models."""
    models = [
        ModelInfo(name="model1"),
        ModelInfo(name="model2"),
    ]

    # Invalid regex: unclosed bracket
    filtered = filter_models(models, r"[invalid")

    assert len(filtered) == 2
    assert filtered == models


def test_get_available_models() -> None:
    """Test getting available models combines local and cloud."""
    local_models = [ModelInfo(name="llama3")]

    mock_response = MagicMock()
    mock_response.json.return_value = {"models": [{"name": "gpt-neo"}]}

    with patch("src.services.model_manager.requests.get", return_value=mock_response):
        result = get_available_models(local_models)

        assert "local" in result
        assert "cloud" in result
        assert len(result["local"]) == 1
        assert len(result["cloud"]) == 1
        assert result["local"][0].name == "llama3"
        assert result["cloud"][0].name == "gpt-neo"
