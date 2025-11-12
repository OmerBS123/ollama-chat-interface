"""
Integration tests for model management workflow.

Tests the complete flow: pull model -> list models -> delete model.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.models.schemas import ModelInfo
from src.services.model_manager import filter_models, list_cloud_models
from src.services.ollama_service import (
    delete_model,
    list_local_models,
    pull_model,
    pull_model_with_progress,
)


@pytest.mark.integration
class TestModelManagementFlow:
    """Integration tests for complete model management workflows."""

    @patch("ollama.list")
    @patch("ollama.pull")
    async def test_pull_and_list_model_flow(self, mock_pull, mock_list):
        """Test pulling a model and then listing it."""
        # Mock pulling a model
        mock_pull.return_value = {"status": "success"}

        # Mock listing models before and after pull
        mock_list.side_effect = [
            # Before pull: empty list
            [],
            # After pull: model appears
            [MagicMock(model="llama3:latest", size=4500000000)],
        ]

        # Step 1: Verify model not in list
        models_before = list_local_models()
        assert len(models_before) == 0

        # Step 2: Pull the model
        await pull_model("llama3")

        # Step 3: Verify model now appears in list
        models_after = list_local_models()
        assert len(models_after) == 1
        assert "llama3" in models_after[0].name

    @patch("ollama.list")
    @patch("ollama.delete")
    def test_list_and_delete_model_flow(self, mock_delete, mock_list):
        """Test listing models and then deleting one."""
        # Mock initial model list with 2 models
        mock_list.side_effect = [
            # Before delete: 2 models
            [
                MagicMock(model="llama3:latest", size=4500000000),
                MagicMock(model="mistral:latest", size=4000000000),
            ],
            # After delete: 1 model remaining
            [MagicMock(model="mistral:latest", size=4000000000)],
        ]

        mock_delete.return_value = {"status": "success"}

        # Step 1: List models before deletion
        models_before = list_local_models()
        assert len(models_before) == 2

        # Step 2: Delete a model
        delete_model("llama3:latest")

        # Step 3: Verify model is removed from list
        models_after = list_local_models()
        assert len(models_after) == 1
        assert "mistral" in models_after[0].name

    @patch("ollama.list")
    @patch("ollama.pull")
    @pytest.mark.asyncio
    async def test_pull_with_progress_tracking(self, mock_pull, mock_list):
        """Test pulling a model with progress tracking."""

        async def mock_progress_generator():
            """Mock progress updates during pull."""
            yield {"status": "downloading", "completed": 1000, "total": 5000}
            yield {"status": "downloading", "completed": 2500, "total": 5000}
            yield {"status": "downloading", "completed": 5000, "total": 5000}
            yield {"status": "success"}

        with patch(
            "src.services.ollama_service.pull_model_with_progress",
            return_value=mock_progress_generator(),
        ):
            progress_updates = []

            async for progress in pull_model_with_progress("llama3"):
                progress_updates.append(progress)

            # Verify we got all progress updates
            assert len(progress_updates) == 4
            assert progress_updates[-1]["status"] == "success"

    @patch("src.services.ollama_service.list_local_models")
    @patch("src.services.model_manager.list_cloud_models")
    def test_filter_local_vs_cloud_models(self, mock_cloud, mock_local):
        """Test filtering between local and cloud models."""
        # Mock local models
        mock_local.return_value = [
            ModelInfo(name="llama3:latest", size=4500000000),
        ]

        # Mock cloud models
        mock_cloud.return_value = [
            ModelInfo(name="llama3:latest", size=4500000000),  # Duplicate
            ModelInfo(name="mistral:latest", size=4000000000),  # Not downloaded
        ]

        # Get models
        local_models = list_local_models()
        cloud_models = list_cloud_models()

        # Filter out already downloaded models from cloud list
        local_names = {m.name for m in local_models}
        available_cloud = [m for m in cloud_models if m.name not in local_names]

        # Verify filtering works
        assert len(available_cloud) == 1
        assert available_cloud[0].name == "mistral:latest"


@pytest.mark.integration
@pytest.mark.slow
class TestModelSearchAndFilter:
    """Integration tests for model search and filtering."""

    @patch("src.services.model_manager.list_cloud_models")
    def test_search_models_by_pattern(self, mock_cloud):
        """Test searching cloud models with regex pattern."""
        # Mock cloud models
        mock_cloud.return_value = [
            ModelInfo(name="llama3:latest"),
            ModelInfo(name="llama3.2:latest"),
            ModelInfo(name="mistral:latest"),
            ModelInfo(name="codellama:7b"),
        ]

        all_models = list_cloud_models()

        # Filter for llama models
        llama_models = filter_models(all_models, r"llama")
        assert len(llama_models) == 3  # llama3, llama3.2, codellama

        # Filter for llama3 specifically
        llama3_models = filter_models(all_models, r"^llama3")
        assert len(llama3_models) == 2  # llama3, llama3.2 only

        # Filter for models with size parameter
        sized_models = filter_models(all_models, r":\d+b")
        assert len(sized_models) == 1  # codellama:7b

    @patch("ollama.list")
    @patch("src.services.model_manager.list_cloud_models")
    def test_combined_local_and_cloud_search(self, mock_cloud, mock_local):
        """Test searching across both local and cloud models."""
        # Mock local models
        mock_local.return_value = [
            MagicMock(model="llama3:latest", size=4500000000),
        ]

        # Mock cloud models
        mock_cloud.return_value = [
            ModelInfo(name="llama3:latest"),  # Also available in cloud
            ModelInfo(name="llama3.2:latest"),  # Cloud only
            ModelInfo(name="mistral:latest"),  # Cloud only
        ]

        local = list_local_models()
        cloud = list_cloud_models()

        # Search for "llama" across both
        local_llama = filter_models(local, r"llama")
        cloud_llama = filter_models(cloud, r"llama")

        # Verify both searches work
        assert len(local_llama) == 1
        assert len(cloud_llama) == 2


@pytest.mark.integration
def test_module_integration():
    """Test that service modules integrate correctly."""
    # Verify imports work across modules
    from src.services import model_manager, ollama_service

    assert callable(ollama_service.list_local_models)
    assert callable(model_manager.list_cloud_models)
    assert callable(model_manager.filter_models)
