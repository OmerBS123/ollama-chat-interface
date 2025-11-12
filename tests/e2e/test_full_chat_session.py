"""
End-to-end tests for complete chat session workflow.

Tests the full user journey from app start to chat completion.
"""

from unittest.mock import patch

import pytest

from src.models.schemas import ChatMessage, ModelParameters
from src.services.ollama_service import chat_stream
from src.services.session_manager import load_session, save_session


@pytest.mark.e2e
class TestFullChatSession:
    """End-to-end tests for complete chat sessions."""

    @pytest.mark.asyncio
    async def test_complete_chat_flow_with_session_save(self):
        """Test full flow: start chat -> send message -> get response -> save session."""

        # Mock Ollama chat stream
        async def mock_chat_generator():
            yield "Hello"
            yield " there!"
            yield " How"
            yield " can"
            yield " I"
            yield " help"
            yield " you"
            yield " today?"

        with patch("ollama.chat", return_value=iter([
            {"message": {"content": "Hello"}},
            {"message": {"content": " there!"}},
            {"message": {"content": " How"}},
            {"message": {"content": " can"}},
            {"message": {"content": " I"}},
            {"message": {"content": " help"}},
            {"message": {"content": " you"}},
            {"message": {"content": " today?"}},
        ])):
            # Step 1: Initialize session state
            model = "llama3"
            params = ModelParameters(temperature=0.7, top_p=0.9)
            messages = []
            system_prompt = "You are a helpful assistant"

            # Step 2: User sends first message
            user_message = "Hello, can you help me with Python?"
            messages.append({"role": "user", "content": user_message})

            # Step 3: Get streaming response
            full_response = ""
            async for chunk in chat_stream(messages, model, params):
                full_response += chunk

            assert full_response == "Hello there! How can I help you today?"

            # Step 4: Add assistant response to history
            messages.append({"role": "assistant", "content": full_response})

            # Step 5: Save session to disk
            chat_messages = [
                ChatMessage(role=msg["role"], content=msg["content"])
                for msg in messages
            ]

            with patch("builtins.open", create=True), \
                 patch("json.dump") as mock_json_dump, \
                 patch("os.makedirs"):

                save_session(
                    session_id="test-session",
                    model_name=model,
                    messages=chat_messages,
                    parameters=params,
                    system_prompt=system_prompt,
                )

                # Verify session was saved
                mock_json_dump.assert_called_once()

            # Step 6: Verify we can load the session back
            with patch("os.path.exists", return_value=True), \
                 patch("builtins.open", create=True), \
                 patch("json.load", return_value={
                     "session_id": "test-session",
                     "model_name": model,
                     "messages": [
                         {"role": "user", "content": user_message, "timestamp": "2025-01-01T00:00:00"},
                         {"role": "assistant", "content": full_response, "timestamp": "2025-01-01T00:00:05"},
                     ],
                     "parameters": {"temperature": 0.7, "top_p": 0.9, "max_tokens": None},
                     "system_prompt": system_prompt,
                     "created_at": "2025-01-01T00:00:00",
                 }):

                loaded_session = load_session("test-session")

                assert loaded_session is not None
                assert loaded_session.model_name == model
                assert len(loaded_session.messages) == 2
                assert loaded_session.messages[0].content == user_message
                assert loaded_session.messages[1].content == full_response

    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self):
        """Test multiple turns of conversation."""

        conversation_history = []
        model = "llama3"
        params = ModelParameters(temperature=0.7, top_p=0.9)

        # Mock different responses for each turn
        responses = [
            ["Hello!", " How", " can", " I", " help?"],
            ["Python", " is", " great", " for", " data", " science."],
            ["You're", " welcome!"],
        ]

        for i, user_msg in enumerate([
            "Hi there!",
            "Tell me about Python.",
            "Thanks!",
        ]):
            # Add user message
            conversation_history.append({"role": "user", "content": user_msg})

            # Mock stream response
            mock_chunks = [{"message": {"content": chunk}} for chunk in responses[i]]

            with patch("ollama.chat", return_value=iter(mock_chunks)):
                # Get assistant response
                full_response = ""
                async for chunk in chat_stream(conversation_history, model, params):
                    full_response += chunk

                # Add to history
                conversation_history.append({"role": "assistant", "content": full_response})

        # Verify full conversation
        assert len(conversation_history) == 6  # 3 user + 3 assistant messages
        assert conversation_history[0]["content"] == "Hi there!"
        assert "help" in conversation_history[1]["content"]
        assert "Python" in conversation_history[3]["content"]

    @pytest.mark.asyncio
    @pytest.mark.requires_ollama
    async def test_file_upload_integration(self):
        """Test uploading a file and discussing it with the model."""

        model = "llama3"
        params = ModelParameters()

        # Simulate file upload
        file_content = """
def hello_world():
    print("Hello, World!")
"""

        user_question = "What does this code do?"
        full_message = f"""{user_question}

---
**Uploaded Files:**

**File: example.py**
```
{file_content}
```
"""

        # Mock response
        mock_response = [
            {"message": {"content": "This"}},
            {"message": {"content": " code"}},
            {"message": {"content": " prints"}},
            {"message": {"content": " 'Hello, World!'"}},
        ]

        with patch("ollama.chat", return_value=iter(mock_response)):
            messages = [{"role": "user", "content": full_message}]

            response = ""
            async for chunk in chat_stream(messages, model, params):
                response += chunk

            assert "Hello, World!" in response or "prints" in response


@pytest.mark.e2e
@pytest.mark.slow
class TestModelSwitchingFlow:
    """Test switching models mid-conversation."""

    @pytest.mark.asyncio
    async def test_switch_model_mid_conversation(self):
        """Test changing model during an active conversation."""

        conversation = []
        params = ModelParameters()

        # Start with llama3
        model1 = "llama3"
        conversation.append({"role": "user", "content": "Hello!"})

        with patch("ollama.chat", return_value=iter([{"message": {"content": "Hi!"}}])):
            response1 = ""
            async for chunk in chat_stream(conversation, model1, params):
                response1 += chunk

            conversation.append({"role": "assistant", "content": response1})

        # Switch to mistral
        model2 = "mistral"
        conversation.append({"role": "user", "content": "Tell me a joke."})

        with patch("ollama.chat", return_value=iter([{"message": {"content": "Why did..."}}])):
            response2 = ""
            async for chunk in chat_stream(conversation, model2, params):
                response2 += chunk

            conversation.append({"role": "assistant", "content": response2})

        # Verify conversation history is maintained across model switches
        assert len(conversation) == 4
        assert conversation[0]["content"] == "Hello!"
        assert conversation[2]["content"] == "Tell me a joke."


@pytest.mark.e2e
def test_end_to_end_module_integration():
    """Test that all modules work together."""
    from src.models import schemas
    from src.services import model_manager, ollama_service, session_manager, system_service

    # Verify all modules are importable and have expected exports
    assert hasattr(ollama_service, "chat_stream")
    assert hasattr(model_manager, "list_cloud_models")
    assert hasattr(session_manager, "save_session")
    assert hasattr(system_service, "shutdown_app")
    assert hasattr(schemas, "ChatMessage")
