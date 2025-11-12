"""
Main Chainlit application entry point.

This module sets up the Chainlit app and imports all handlers.
"""

# Initialize logging first (before any other imports that might use logging)
from .config.logging import setup_logging
from .config.settings import get_settings

settings = get_settings()
setup_logging(log_level=settings.log_level, log_dir=settings.log_dir)

# Now we can use logging
import logging

logger = logging.getLogger(__name__)

logger.info("=" * 60)
logger.info("Chainlit OSS Chatbot Application Starting")
logger.info("=" * 60)
logger.info(f"Log level: {settings.log_level}")
logger.info(f"Log directory: {settings.log_dir}")
logger.info(f"Default model: {settings.default_model}")
logger.debug(f"Settings: {settings}")


# Data layer registration DISABLED to remove left sidebar
# The "View History" button provides full history management without the sidebar
# Uncomment the code below to re-enable the left sidebar:
#
# @cl.data_layer
# def init_data_layer():
#     """Initialize the JSON-based data layer for chat history persistence."""
#     logger.info("Initializing data layer for chat history sidebar")
#     return JSONDataLayer()

logger.info("Data layer disabled - using button-only history management")


# Chat resume handler DISABLED (only needed for left sidebar)
# The "View History" button handles loading conversations directly
# Uncomment the code below to re-enable:
#
# @cl.on_chat_resume
# async def on_chat_resume(thread: ThreadDict):
#     """
#     Handle resuming a previous chat thread.
#
#     Called when user clicks on a conversation in the left sidebar.
#     """
#     thread_id = thread.get("id", "")
#     thread_name = thread.get("name", "Unknown")
#     logger.info(f"Resuming chat thread: {thread_id} ('{thread_name}')")
#
#     # Load the session from storage
#     from .services.session_manager import load_session
#
#     session = load_session(thread_id)
#     if not session:
#         logger.error(f"Failed to load session {thread_id}")
#         await cl.Message(content=f"❌ **Error:** Could not load session {thread_id}").send()
#         return
#
#     logger.info(f"Loaded session: {len(session.messages)} messages, model={session.model_name}")
#
#     # Restore session state
#     cl.user_session.set("model", session.model_name)
#     cl.user_session.set("parameters", session.parameters)
#     cl.user_session.set("system_prompt", session.system_prompt)
#
#     # Convert ChatMessage objects to dict format for session storage
#     messages = [{"role": msg.role, "content": msg.content} for msg in session.messages]
#     cl.user_session.set("messages", messages)
#
#     logger.debug(
#         f"Restored session state: model={session.model_name}, "
#         f"messages={len(messages)}, has_system_prompt={session.system_prompt is not None}"
#     )
#
#     # Display the conversation history
#     logger.info("Displaying conversation history in chat")
#     await cl.Message(
#         content=f"✅ **Resumed conversation:** {thread_name}\n\n"
#         f"**Model:** {session.model_name}\n"
#         f"**Messages:** {len(session.messages)}\n"
#         f"**Created:** {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
#     ).send()
#
#     # Display each message in the thread
#     for msg in session.messages:
#         role_emoji = "👤" if msg.role == "user" else "🤖"
#         await cl.Message(content=f"{role_emoji} **{msg.role.title()}:** {msg.content}").send()
#
#     logger.info(f"Successfully resumed chat thread {thread_id}")

logger.info("Chat resume handler disabled - left sidebar will not be shown")


# Import all handlers to register them with Chainlit
logger.debug("Importing UI handlers...")
from .ui import (
    actions,
    chat,
    chat_profiles,
    model_management,
    model_management_button,
    system_actions,
)
from .ui import (
    settings as ui_settings,
)

logger.info("UI handlers imported successfully")
logger.debug(
    "Registered handlers: chat, chat_profiles, settings, actions, model_management, "
    "model_management_button, system_actions"
)
logger.info("Application initialization complete")

# Re-export for clarity
__all__ = [
    "chat",
    "chat_profiles",
    "ui_settings",
    "actions",
    "model_management",
    "model_management_button",
    "system_actions",
]
