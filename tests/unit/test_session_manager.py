"""
Tests for session_manager module.
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from src.models.schemas import ChatMessage, ModelParameters
from src.services.session_manager import delete_session, list_sessions, load_session, save_session


@pytest.fixture
def temp_session_dir(tmp_path: Path) -> Path:
    """Create temporary session directory."""
    session_dir = tmp_path / "sessions"
    session_dir.mkdir()
    return session_dir


def test_save_session(temp_session_dir: Path) -> None:
    """Test saving a session creates JSON file."""
    with patch("src.services.session_manager.get_settings") as mock_settings:
        mock_settings.return_value.session_data_dir = temp_session_dir

        messages = [
            ChatMessage(role="user", content="Hello", timestamp=datetime.now()),
            ChatMessage(role="assistant", content="Hi!", timestamp=datetime.now()),
        ]
        params = ModelParameters()

        save_session("test_session", "llama3", messages, params, "You are helpful")

        session_file = temp_session_dir / "test_session.json"
        assert session_file.exists()

        # Verify JSON content
        with open(session_file) as f:
            data = json.load(f)
            assert data["session_id"] == "test_session"
            assert data["model_name"] == "llama3"
            assert len(data["messages"]) == 2
            assert data["system_prompt"] == "You are helpful"


def test_load_session(temp_session_dir: Path) -> None:
    """Test loading a session retrieves correct data."""
    with patch("src.services.session_manager.get_settings") as mock_settings:
        mock_settings.return_value.session_data_dir = temp_session_dir

        # First save a session
        messages = [
            ChatMessage(role="user", content="Test", timestamp=datetime.now()),
        ]
        params = ModelParameters(temperature=0.5)
        save_session("test_load", "mistral", messages, params)

        # Then load it
        session = load_session("test_load")

        assert session is not None
        assert session.session_id == "test_load"
        assert session.model_name == "mistral"
        assert len(session.messages) == 1
        assert session.parameters.temperature == 0.5


def test_load_session_not_found(temp_session_dir: Path) -> None:
    """Test loading non-existent session returns None."""
    with patch("src.services.session_manager.get_settings") as mock_settings:
        mock_settings.return_value.session_data_dir = temp_session_dir

        session = load_session("nonexistent")
        assert session is None


def test_list_sessions(temp_session_dir: Path) -> None:
    """Test listing sessions returns all session IDs."""
    with patch("src.services.session_manager.get_settings") as mock_settings:
        mock_settings.return_value.session_data_dir = temp_session_dir

        # Create multiple sessions
        messages = [ChatMessage(role="user", content="Test", timestamp=datetime.now())]
        params = ModelParameters()

        save_session("session1", "llama3", messages, params)
        save_session("session2", "mistral", messages, params)
        save_session("session3", "gemma", messages, params)

        sessions = list_sessions()

        assert len(sessions) == 3
        assert "session1" in sessions
        assert "session2" in sessions
        assert "session3" in sessions


def test_delete_session(temp_session_dir: Path) -> None:
    """Test deleting a session removes the file."""
    with patch("src.services.session_manager.get_settings") as mock_settings:
        mock_settings.return_value.session_data_dir = temp_session_dir

        # Create a session
        messages = [ChatMessage(role="user", content="Test", timestamp=datetime.now())]
        params = ModelParameters()
        save_session("to_delete", "llama3", messages, params)

        # Verify it exists
        assert (temp_session_dir / "to_delete.json").exists()

        # Delete it
        result = delete_session("to_delete")

        assert result is True
        assert not (temp_session_dir / "to_delete.json").exists()


def test_delete_session_not_found(temp_session_dir: Path) -> None:
    """Test deleting non-existent session returns False."""
    with patch("src.services.session_manager.get_settings") as mock_settings:
        mock_settings.return_value.session_data_dir = temp_session_dir

        result = delete_session("nonexistent")
        assert result is False


def test_save_session_preserves_created_at(temp_session_dir: Path) -> None:
    """Test updating a session preserves original created_at timestamp."""
    with patch("src.services.session_manager.get_settings") as mock_settings:
        mock_settings.return_value.session_data_dir = temp_session_dir

        messages = [ChatMessage(role="user", content="Test", timestamp=datetime.now())]
        params = ModelParameters()

        # Save initial session
        save_session("update_test", "llama3", messages, params)
        first_session = load_session("update_test")
        assert first_session is not None
        original_created_at = first_session.created_at

        # Update session with new message
        messages.append(ChatMessage(role="assistant", content="Response", timestamp=datetime.now()))
        save_session("update_test", "llama3", messages, params)
        updated_session = load_session("update_test")

        assert updated_session is not None
        assert updated_session.created_at == original_created_at
        assert len(updated_session.messages) == 2
