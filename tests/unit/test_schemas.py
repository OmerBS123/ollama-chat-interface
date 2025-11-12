"""
Unit tests for Pydantic schemas/models.

Tests data validation for ChatMessage, ModelInfo, and ModelParameters.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.models.schemas import ChatMessage, ChatSession, ModelInfo, ModelParameters


class TestChatMessage:
    """Tests for ChatMessage model."""

    def test_valid_user_message(self):
        """Test creating a valid user message."""
        msg = ChatMessage(role="user", content="Hello!")

        assert msg.role == "user"
        assert msg.content == "Hello!"
        assert isinstance(msg.timestamp, datetime)

    def test_valid_assistant_message(self):
        """Test creating a valid assistant message."""
        msg = ChatMessage(role="assistant", content="Hi there!")

        assert msg.role == "assistant"
        assert msg.content == "Hi there!"

    def test_valid_system_message(self):
        """Test creating a valid system message."""
        msg = ChatMessage(role="system", content="You are helpful.")

        assert msg.role == "system"
        assert msg.content == "You are helpful."

    def test_invalid_role(self):
        """Test that invalid roles are rejected."""
        with pytest.raises(ValidationError):
            ChatMessage(role="invalid", content="test")

    def test_empty_content(self):
        """Test that empty content is allowed."""
        msg = ChatMessage(role="user", content="")
        assert msg.content == ""

    def test_custom_timestamp(self):
        """Test providing custom timestamp."""
        custom_time = datetime(2025, 1, 1, 12, 0, 0)
        msg = ChatMessage(role="user", content="test", timestamp=custom_time)

        assert msg.timestamp == custom_time


class TestModelParameters:
    """Tests for ModelParameters model."""

    def test_valid_parameters(self):
        """Test creating valid model parameters."""
        params = ModelParameters(
            temperature=0.7,
            top_p=0.9,
            max_tokens=2000
        )

        assert params.temperature == 0.7
        assert params.top_p == 0.9
        assert params.max_tokens == 2000

    def test_temperature_validation_min(self):
        """Test temperature minimum constraint."""
        with pytest.raises(ValidationError):
            ModelParameters(temperature=-0.1, top_p=0.9)

    def test_temperature_validation_max(self):
        """Test temperature maximum constraint."""
        with pytest.raises(ValidationError):
            ModelParameters(temperature=2.1, top_p=0.9)

    def test_top_p_validation_min(self):
        """Test top_p minimum constraint."""
        with pytest.raises(ValidationError):
            ModelParameters(temperature=0.7, top_p=-0.1)

    def test_top_p_validation_max(self):
        """Test top_p maximum constraint."""
        with pytest.raises(ValidationError):
            ModelParameters(temperature=0.7, top_p=1.1)

    def test_max_tokens_validation_min(self):
        """Test max_tokens minimum constraint."""
        with pytest.raises(ValidationError):
            ModelParameters(temperature=0.7, top_p=0.9, max_tokens=0)

    def test_max_tokens_none_allowed(self):
        """Test that max_tokens can be None (unlimited)."""
        params = ModelParameters(temperature=0.7, top_p=0.9, max_tokens=None)
        assert params.max_tokens is None

    def test_default_values(self):
        """Test that defaults are applied correctly."""
        params = ModelParameters()

        assert params.temperature == 0.7
        assert params.top_p == 0.9
        assert params.max_tokens is None


class TestModelInfo:
    """Tests for ModelInfo model."""

    def test_valid_model_info(self):
        """Test creating valid model info."""
        info = ModelInfo(
            name="llama3:latest",
            size=4500000000,
            family="llama"
        )

        assert info.name == "llama3:latest"
        assert info.size == 4500000000
        assert info.family == "llama"

    def test_model_info_with_minimal_data(self):
        """Test creating model info with only name."""
        info = ModelInfo(name="mistral")

        assert info.name == "mistral"
        assert info.size is None
        assert info.family is None

    def test_model_info_size_formatting(self):
        """Test size formatting helper (if exists)."""
        info = ModelInfo(
            name="llama3",
            size=4_500_000_000,  # 4.5GB
        )

        assert info.size == 4_500_000_000
        # Test formatting to GB
        size_gb = info.size / (1024**3)
        assert round(size_gb, 2) == 4.19  # 4500000000 bytes ≈ 4.19 GB


class TestChatSession:
    """Tests for ChatSession model."""

    def test_valid_chat_session(self):
        """Test creating a valid chat session."""
        messages = [
            ChatMessage(role="user", content="Hello"),
            ChatMessage(role="assistant", content="Hi!"),
        ]
        params = ModelParameters(temperature=0.7, top_p=0.9)

        session = ChatSession(
            session_id="test-123",
            model_name="llama3",
            messages=messages,
            parameters=params,
            system_prompt="You are helpful",
        )

        assert session.session_id == "test-123"
        assert session.model_name == "llama3"
        assert len(session.messages) == 2
        assert session.parameters.temperature == 0.7
        assert session.system_prompt == "You are helpful"
        assert isinstance(session.created_at, datetime)

    def test_chat_session_without_system_prompt(self):
        """Test chat session without system prompt."""
        messages = [ChatMessage(role="user", content="test")]
        params = ModelParameters()

        session = ChatSession(
            session_id="test",
            model_name="llama3",
            messages=messages,
            parameters=params,
        )

        assert session.system_prompt is None

    def test_chat_session_empty_messages(self):
        """Test chat session with no messages."""
        session = ChatSession(
            session_id="test",
            model_name="llama3",
            messages=[],
            parameters=ModelParameters(),
        )

        assert len(session.messages) == 0


@pytest.mark.unit
def test_module_exports():
    """Test that all expected models are exported."""
    from src.models import schemas

    assert hasattr(schemas, "ChatMessage")
    assert hasattr(schemas, "ModelInfo")
    assert hasattr(schemas, "ModelParameters")
    assert hasattr(schemas, "ChatSession")
