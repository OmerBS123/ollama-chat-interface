"""
Chat history button and management UI.

Provides a visual interface for viewing, loading, and deleting past conversations
without requiring authentication.
"""

import logging

import chainlit as cl

from ..services.session_manager import delete_session, list_sessions_detailed, load_session

logger = logging.getLogger(__name__)


def get_history_button() -> cl.Action:
    """
    Create the View History action button.

    Returns:
        Action button for viewing chat history
    """
    logger.debug("Creating history button")
    return cl.Action(
        name="view_history",
        label="📚 View History",
        description="View and manage past conversations",
        payload={},
    )


async def show_history_list() -> None:
    """
    Display a formatted list of all saved conversations.

    Shows each conversation with preview, metadata, and action buttons.
    """
    logger.info("User requested history view")

    # Get all saved sessions
    sessions = list_sessions_detailed()
    logger.info(f"Displaying {len(sessions)} conversation(s)")

    # Handle empty state
    if not sessions:
        logger.info("No conversations found")
        await cl.Message(
            content="## 📚 Chat History\n\n"
            "**No saved conversations yet.**\n\n"
            "Start chatting to create your first conversation!\n\n",
            actions=[
                cl.Action(
                    name="close_history",
                    label="❌ Close",
                    description="Close history view",
                    payload={},
                )
            ],
        ).send()
        return

    # Build the message content
    message_lines = [
        f"## 📚 Chat History ({len(sessions)} conversation{'s' if len(sessions) != 1 else ''})\n",
    ]

    # Create actions list for all conversations
    actions = []

    # Add each conversation
    for i, session in enumerate(sessions):
        # Format timestamps
        created = session["created_at"].strftime("%Y-%m-%d %H:%M")
        updated = session["updated_at"].strftime("%Y-%m-%d %H:%M")

        # Add conversation card
        message_lines.append(f"### 📝 {session['preview']}")
        message_lines.append(f"**Model:** {session['model']}  ")
        message_lines.append(f"**Messages:** {session['message_count']}  ")
        message_lines.append(f"**Created:** {created}  ")
        message_lines.append(f"**Updated:** {updated}  ")
        message_lines.append("")  # Blank line

        # Create action buttons for this conversation
        session_id = session["session_id"]
        actions.extend(
            [
                cl.Action(
                    name=f"load_conv_{session_id}",
                    label=f"📂 Load #{i + 1}",
                    description=f"Load: {session['preview'][:30]}",
                    payload={"session_id": session_id},
                ),
                cl.Action(
                    name=f"delete_conv_{session_id}",
                    label=f"🗑️ Delete #{i + 1}",
                    description=f"Delete: {session['preview'][:30]}",
                    payload={"session_id": session_id},
                ),
            ]
        )

        # Add separator between conversations
        if i < len(sessions) - 1:
            message_lines.append("---\n")

    # Add footer actions
    actions.extend(
        [
            cl.Action(
                name="refresh_history",
                label="🔄 Refresh",
                description="Refresh conversation list",
                payload={},
            ),
            cl.Action(
                name="close_history",
                label="❌ Close",
                description="Close history view",
                payload={},
            ),
        ]
    )

    # Send the message with all actions
    content = "\n".join(message_lines)
    await cl.Message(content=content, actions=actions).send()
    logger.debug(f"Displayed history list with {len(actions)} action buttons")


@cl.action_callback("view_history")
async def on_view_history(action: cl.Action) -> None:
    """
    Handle View History button click.

    Displays the list of all saved conversations.
    """
    logger.info("View History button clicked")
    await show_history_list()


@cl.action_callback("load_conv_*")
async def on_load_conversation(action: cl.Action) -> None:
    """
    Handle Load Conversation button click.

    Loads the selected conversation into the current session.
    """
    session_id = action.payload.get("session_id")
    logger.info(f"Loading conversation: {session_id}")

    # Load session from disk
    session = load_session(session_id)

    if not session:
        logger.error(f"Failed to load conversation {session_id}")
        await cl.Message(content=f"❌ **Error:** Could not load conversation `{session_id}`").send()
        return

    logger.info(
        f"Loaded conversation: {len(session.messages)} messages, model={session.model_name}"
    )

    # Update current session state
    cl.user_session.set("model", session.model_name)
    cl.user_session.set("parameters", session.parameters)
    cl.user_session.set("system_prompt", session.system_prompt)

    # Convert ChatMessage objects to dict format for session storage
    messages = [{"role": msg.role, "content": msg.content} for msg in session.messages]
    cl.user_session.set("messages", messages)

    logger.debug(
        f"Restored session state: model={session.model_name}, "
        f"messages={len(messages)}, has_system_prompt={session.system_prompt is not None}"
    )

    # Display success message
    await cl.Message(
        content=f"✅ **Loaded conversation**\n\n"
        f"**Preview:** {session.messages[0].content[:50] if session.messages else 'N/A'}\n"
        f"**Model:** {session.model_name}\n"
        f"**Messages:** {len(session.messages)}\n"
        f"**Created:** {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"---\n\n"
        f"**Conversation history:**"
    ).send()

    # Display each message in the conversation
    for msg in session.messages:
        role_emoji = "👤" if msg.role == "user" else "🤖"
        await cl.Message(content=f"{role_emoji} **{msg.role.title()}:** {msg.content}").send()

    logger.info(f"Successfully loaded and displayed conversation {session_id}")


@cl.action_callback("delete_conv_*")
async def on_delete_conversation(action: cl.Action) -> None:
    """
    Handle Delete Conversation button click.

    Shows confirmation dialog before deleting.
    """
    session_id = action.payload.get("session_id")
    logger.info(f"Delete request for conversation: {session_id}")

    # Load session to show preview
    session = load_session(session_id)
    if not session:
        logger.error(f"Cannot delete - conversation {session_id} not found")
        await cl.Message(content=f"❌ **Error:** Conversation `{session_id}` not found").send()
        return

    preview = session.messages[0].content[:50] if session.messages else "N/A"

    # Ask for confirmation
    logger.debug(f"Showing delete confirmation for: {preview}")
    res = await cl.AskActionMessage(
        content=f"⚠️ **Delete Conversation?**\n\n"
        f"**Preview:** {preview}\n"
        f"**Messages:** {len(session.messages)}\n\n"
        f"This action **cannot be undone**.",
        actions=[
            cl.Action(
                name=f"confirm_delete_{session_id}",
                label="🗑️ Yes, Delete",
                description="Confirm deletion",
                payload={"session_id": session_id},
            ),
            cl.Action(
                name="cancel_delete",
                label="❌ Cancel",
                description="Cancel deletion",
                payload={},
            ),
        ],
    ).send()

    # Handle response
    if res and res.get("name", "").startswith("confirm_delete"):
        logger.info(f"User confirmed deletion of {session_id}")
        await on_confirm_delete(res)
    else:
        logger.info(f"User cancelled deletion of {session_id}")
        await cl.Message(content="✅ Deletion cancelled").send()


@cl.action_callback("confirm_delete_*")
async def on_confirm_delete(action: cl.Action) -> None:
    """
    Handle confirmed deletion of a conversation.

    Deletes the conversation and refreshes the history list.
    """
    session_id = action.payload.get("session_id")
    logger.info(f"Deleting conversation: {session_id}")

    # Delete session from disk
    success = delete_session(session_id)

    if success:
        logger.info(f"Successfully deleted conversation {session_id}")
        await cl.Message(content="✅ **Conversation deleted successfully**").send()

        # Refresh the history list
        logger.debug("Refreshing history list after deletion")
        await show_history_list()
    else:
        logger.error(f"Failed to delete conversation {session_id}")
        await cl.Message(
            content=f"❌ **Error:** Failed to delete conversation `{session_id}`"
        ).send()


@cl.action_callback("cancel_delete")
async def on_cancel_delete(action: cl.Action) -> None:
    """
    Handle cancellation of delete operation.
    """
    logger.debug("Delete operation cancelled")
    await cl.Message(content="✅ Deletion cancelled").send()


@cl.action_callback("refresh_history")
async def on_refresh_history(action: cl.Action) -> None:
    """
    Handle Refresh History button click.

    Reloads and displays the conversation list.
    """
    logger.info("Refresh History button clicked")
    await show_history_list()


@cl.action_callback("close_history")
async def on_close_history(action: cl.Action) -> None:
    """
    Handle Close History button click.

    Closes the history view.
    """
    logger.info("Close History button clicked")
    await cl.Message(content="📚 History view closed").send()
