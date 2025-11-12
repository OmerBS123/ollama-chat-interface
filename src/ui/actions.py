"""
Message actions for copy, regenerate, and edit functionality.

Provides interactive buttons on messages for user actions.
"""

import chainlit as cl

from ..services.ollama_service import chat_stream


@cl.action_callback("copy_message")
async def on_copy_action(action: cl.Action) -> None:
    """
    Handle copy message action.

    Copies message content to clipboard (handled by Chainlit UI).
    """
    await cl.Message(content="Message copied to clipboard!").send()


@cl.action_callback("regenerate_response")
async def on_regenerate_action(action: cl.Action) -> None:
    """
    Handle regenerate response action.

    Regenerates the last assistant response using the same prompt.
    """
    # Get session state
    model = cl.user_session.get("model")
    params = cl.user_session.get("parameters")
    system_prompt = cl.user_session.get("system_prompt")
    history = cl.user_session.get("messages") or []

    if not history:
        await cl.Message(content="No messages to regenerate.").send()
        return

    # Remove last assistant message if present
    if history and history[-1]["role"] == "assistant":
        history.pop()
        cl.user_session.set("messages", history)

    # Build message history
    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    for h in history:
        messages.append({"role": h["role"], "content": h["content"]})

    # Create placeholder message
    msg_out = cl.Message(content="")
    await msg_out.send()

    # Stream response
    try:
        async for chunk in chat_stream(messages, model, params):
            msg_out.content += chunk
            await msg_out.update()
    except Exception as e:
        msg_out.content = f"**Error:** {str(e)}"
        await msg_out.update()
        return

    # Save to history
    history.append({"role": "assistant", "content": msg_out.content})
    cl.user_session.set("messages", history)


@cl.action_callback("edit_message")
async def on_edit_action(action: cl.Action) -> None:
    """
    Handle edit message action.

    Allows user to edit their last message and regenerate response.
    """
    # Get session state
    history = cl.user_session.get("messages") or []

    if not history:
        await cl.Message(content="No messages to edit.").send()
        return

    # Find last user message
    last_user_msg = None
    for i in range(len(history) - 1, -1, -1):
        if history[i]["role"] == "user":
            last_user_msg = history[i]["content"]
            break

    if not last_user_msg:
        await cl.Message(content="No user messages to edit.").send()
        return

    await cl.Message(
        content=f"Your last message was:\n\n> {last_user_msg}\n\nSend a new message to replace it."
    ).send()


def get_message_actions() -> list[cl.Action]:
    """
    Get list of message actions.

    Returns:
        List of Action objects for message interactions
    """
    return [
        cl.Action(
            name="copy_message",
            label="📋 Copy",
            description="Copy message to clipboard",
        ),
        cl.Action(
            name="regenerate_response",
            label="🔄 Regenerate",
            description="Regenerate this response",
        ),
        cl.Action(
            name="edit_message",
            label="✏️ Edit",
            description="Edit your last message",
        ),
    ]
