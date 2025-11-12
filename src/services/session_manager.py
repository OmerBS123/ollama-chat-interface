"""
Session manager for chat history persistence.

Handles saving and loading chat sessions to/from JSON files with organized
directory structure by date.
"""

import json
import logging
from datetime import datetime

from ..config.settings import get_settings
from ..models.schemas import ChatMessage, ChatSession, ModelParameters

logger = logging.getLogger(__name__)


def save_session(
    session_id: str,
    model_name: str,
    messages: list[ChatMessage],
    parameters: ModelParameters,
    system_prompt: str | None = None,
) -> None:
    """
    Save a chat session to disk.

    Args:
        session_id: Unique session identifier
        model_name: Name of the model used
        messages: List of chat messages
        parameters: Model parameters used
        system_prompt: Optional system prompt
    """
    logger.info(f"Saving session: {session_id}")
    logger.debug(
        f"Session details: model={model_name}, "
        f"messages_count={len(messages)}, "
        f"has_system_prompt={system_prompt is not None}"
    )

    settings = get_settings()
    session_path = settings.session_data_dir / f"{session_id}.json"
    logger.debug(f"Session path: {session_path}")

    # Check if session already exists to preserve created_at
    created_at = datetime.now()
    if session_path.exists():
        logger.debug(f"Session {session_id} already exists, preserving created_at timestamp")
        try:
            existing = load_session(session_id)
            if existing:
                created_at = existing.created_at
                logger.debug(f"Preserved created_at: {created_at}")
        except Exception as e:
            logger.warning(f"Could not load existing session to preserve timestamp: {e}")
            pass  # Use new timestamp if we can't load existing

    session = ChatSession(
        session_id=session_id,
        model_name=model_name,
        messages=messages,
        parameters=parameters,
        system_prompt=system_prompt,
        created_at=created_at,
        updated_at=datetime.now(),
    )
    logger.debug(
        f"Created session object: created_at={created_at}, updated_at={session.updated_at}"
    )

    try:
        # Save to JSON file
        with open(session_path, "w") as f:
            json.dump(session.model_dump(mode="json"), f, indent=2, default=str)
        logger.info(f"Successfully saved session {session_id} to {session_path}")
    except Exception as e:
        logger.error(f"Failed to save session {session_id}: {e}", exc_info=True)
        raise


def load_session(session_id: str) -> ChatSession | None:
    """
    Load a chat session from disk.

    Args:
        session_id: Unique session identifier

    Returns:
        ChatSession object if found, None otherwise
    """
    logger.info(f"Loading session: {session_id}")
    settings = get_settings()
    session_path = settings.session_data_dir / f"{session_id}.json"
    logger.debug(f"Session path: {session_path}")

    if not session_path.exists():
        logger.warning(f"Session {session_id} not found at {session_path}")
        return None

    try:
        with open(session_path) as f:
            data = json.load(f)
            logger.debug(f"Loaded session data: {len(data.get('messages', []))} messages")
            session = ChatSession(**data)
            logger.info(
                f"Successfully loaded session {session_id} "
                f"(model: {session.model_name}, "
                f"messages: {len(session.messages)})"
            )
            return session
    except Exception as e:
        logger.error(f"Error loading session {session_id}: {e}", exc_info=True)
        return None


def list_sessions() -> list[str]:
    """
    List all available session IDs.

    Returns:
        List of session IDs (without .json extension)
    """
    logger.debug("Listing all available sessions")
    settings = get_settings()
    session_dir = settings.session_data_dir
    logger.debug(f"Scanning session directory: {session_dir}")

    session_files = list(session_dir.glob("*.json"))
    session_ids = [f.stem for f in session_files]

    logger.info(f"Found {len(session_ids)} session(s)")
    logger.debug(f"Session IDs: {session_ids}")

    return session_ids


def delete_session(session_id: str) -> bool:
    """
    Delete a chat session from disk.

    Args:
        session_id: Unique session identifier

    Returns:
        True if deleted, False if not found
    """
    logger.info(f"Deleting session: {session_id}")
    settings = get_settings()
    session_path = settings.session_data_dir / f"{session_id}.json"
    logger.debug(f"Session path: {session_path}")

    if not session_path.exists():
        logger.warning(f"Session {session_id} not found, cannot delete")
        return False

    try:
        session_path.unlink()
        logger.info(f"Successfully deleted session {session_id}")
        return True
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}", exc_info=True)
        return False


def get_session_preview(session: ChatSession, max_length: int = 50) -> str:
    """
    Generate a preview string from the first user message.

    Args:
        session: ChatSession object
        max_length: Maximum length of preview string

    Returns:
        Preview string (truncated if needed)
    """
    logger.debug(f"Generating preview for session {session.session_id}")

    # Find first user message
    for msg in session.messages:
        if msg.role == "user":
            preview = msg.content.strip().replace("\n", " ")
            if len(preview) > max_length:
                preview = preview[:max_length] + "..."
            logger.debug(f"Generated preview: {preview}")
            return preview

    # Fallback to session ID if no user messages
    logger.debug("No user messages found, using session ID as preview")
    return session.session_id


def list_sessions_detailed() -> list[dict]:
    """
    List all sessions with detailed metadata.

    Returns:
        List of dicts with session details: {
            'session_id': str,
            'preview': str,
            'message_count': int,
            'model': str,
            'created_at': datetime,
            'updated_at': datetime
        }
    """
    logger.debug("Listing all sessions with detailed metadata")
    session_ids = list_sessions()
    detailed_sessions = []

    for session_id in session_ids:
        try:
            session = load_session(session_id)
            if session:
                preview = get_session_preview(session)
                detailed_sessions.append(
                    {
                        "session_id": session_id,
                        "preview": preview,
                        "message_count": len(session.messages),
                        "model": session.model_name,
                        "created_at": session.created_at,
                        "updated_at": session.updated_at,
                    }
                )
                logger.debug(f"Added session {session_id} to detailed list")
        except Exception as e:
            logger.error(f"Error loading session {session_id} for detailed list: {e}")
            continue

    # Sort by updated_at descending (newest first)
    detailed_sessions.sort(key=lambda x: x["updated_at"], reverse=True)

    logger.info(f"Found {len(detailed_sessions)} sessions with details")
    return detailed_sessions


def generate_session_id() -> str:
    """
    Generate a unique session ID based on current timestamp.

    Returns:
        Session ID in format: YYYY-MM-DD_HH-MM-SS
    """
    session_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logger.debug(f"Generated session ID: {session_id}")
    return session_id
