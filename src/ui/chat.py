"""
Chat interface handlers.

Handles chat start, message processing, and streaming responses.
"""

import logging

import chainlit as cl

from ..config.settings import get_settings
from ..models.schemas import ChatMessage, ModelParameters
from ..services.ollama_service import (
    OllamaNotRunningError,
    chat_stream,
    list_local_models,
    pull_model_with_progress,
)
from ..services.session_manager import save_session
from .model_management import handle_model_command
from .model_management_button import get_model_management_button
from .settings import get_settings_config
from .system_actions import get_system_actions, handle_system_command

logger = logging.getLogger(__name__)


@cl.on_chat_start
async def on_chat_start() -> None:
    """
    Initialize chat session.

    Sets up default model, parameters, and greets the user.
    Now integrates with chat profiles for model selection.
    """
    logger.info("Chat session started")
    settings = get_settings()

    # Use Chainlit's thread_id for session management
    thread_id = cl.context.session.thread_id
    logger.info(f"Thread ID from Chainlit: {thread_id}")

    # Check if a chat profile is selected, otherwise use default
    chat_profile = cl.user_session.get("chat_profile")
    if chat_profile:
        selected_model = chat_profile
        logger.info(f"Using chat profile model: {selected_model}")
    else:
        selected_model = settings.default_model
        logger.info(f"No chat profile selected, using default: {selected_model}")

    logger.debug(f"Initializing with model: {selected_model}")

    # Initialize session variables
    cl.user_session.set("model", selected_model)
    cl.user_session.set(
        "parameters",
        ModelParameters(
            temperature=settings.default_temperature,
            top_p=settings.default_top_p,
            max_tokens=settings.default_max_tokens,
        ),
    )
    cl.user_session.set("system_prompt", None)
    cl.user_session.set("messages", [])
    logger.debug(
        f"Session initialized: thread_id={thread_id}, temp={settings.default_temperature}, "
        f"top_p={settings.default_top_p}, max_tokens={settings.default_max_tokens}"
    )

    # Initialize settings sidebar with current session values (optional - now less prominent)
    logger.debug("Preparing to initialize settings sidebar")
    model = cl.user_session.get("model")
    params = cl.user_session.get("parameters")
    system_prompt = cl.user_session.get("system_prompt")

    logger.debug(
        f"Current session values for settings: model={model}, "
        f"params={params}, system_prompt={'set' if system_prompt else 'not set'}"
    )

    try:
        settings_config = get_settings_config(model, params, system_prompt)
        await cl.ChatSettings(settings_config).send()
        logger.info("Settings sidebar initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize settings sidebar: {e}", exc_info=True)
        # Don't raise - settings are now optional since we have chat profiles

    # Try to list local models
    try:
        logger.debug("Attempting to list local models")
        models = list_local_models()
        model_names = [m.name for m in models]
        logger.info(f"Successfully listed {len(model_names)} local models")

        if model_names:
            # Check if selected model is available
            if selected_model in model_names:
                welcome_msg = (
                    f"Welcome! I'm your local LLM assistant.\n\n"
                    f"Current model: **{selected_model}**\n\n"
                    f"💡 **Tips:**\n"
                    f"- Use the **model selector** above the input to switch models\n"
                    f"- Type `/models help` for model management commands\n"
                    f"- Check the **left sidebar** to view and resume past conversations\n"
                    f"- Type `/exit` or `/quit` to exit the application\n\n"
                    f"Start chatting below!"
                )
                logger.debug("Sending welcome message - model available")
            else:
                # Model not downloaded - offer auto-download
                logger.warning(f"Selected model '{selected_model}' not available locally")

                welcome_msg = (
                    f"Welcome! I'm your local LLM assistant.\n\n"
                    f"📥 **Model '{selected_model}' is not downloaded yet.**\n\n"
                    f"Downloading it now... This may take a few minutes depending on model size.\n\n"
                    f"💡 **Tips:**\n"
                    f"- You can switch to a downloaded model using the dropdown above\n"
                    f"- Type `/models list` to see your local models"
                )

                # Send welcome message first
                actions = get_system_actions() + [get_model_management_button()]
                await cl.Message(content=welcome_msg, actions=actions).send()

                # Auto-download the model
                logger.info(f"Auto-downloading model: {selected_model}")
                download_msg = cl.Message(content="")
                await download_msg.send()

                try:
                    download_msg.content = f"📦 **Downloading {selected_model}...**\n\nInitializing..."
                    await download_msg.update()

                    # Pull the model with progress
                    last_status = ""
                    async for progress in pull_model_with_progress(selected_model):
                        # Extract progress info (handle None values)
                        status = progress.get("status", "")
                        completed = progress.get("completed") or 0  # Handle None
                        total = progress.get("total") or 1          # Handle None

                        # Calculate percentage
                        if total and total > 0:
                            percentage = int((completed / total) * 100)
                        else:
                            percentage = 0

                        # Create visual progress bar
                        bar_length = 20
                        filled = int(bar_length * percentage / 100)
                        bar = "█" * filled + "░" * (bar_length - filled)

                        # Format sizes in GB (handle None values)
                        completed_gb = (completed or 0) / (1024**3)  # bytes to GB
                        total_gb = (total or 1) / (1024**3)

                        # Build progress message
                        progress_text = (
                            f"📦 **Downloading {selected_model}...**\n\n"
                            f"**Progress:** {percentage}%\n\n"
                            f"`{bar}`\n\n"
                        )

                        # Add size info if available
                        if total and total > 0:
                            progress_text += f"**Size:** {completed_gb:.2f} GB / {total_gb:.2f} GB\n\n"

                        # Add status if it changed
                        if status and status != last_status:
                            progress_text += f"**Status:** {status}\n"
                            last_status = status

                        download_msg.content = progress_text
                        await download_msg.update()

                    download_msg.content = (
                        f"✅ **Download complete!**\n\n"
                        f"Model **{selected_model}** is now ready to use.\n\n"
                        f"You can start chatting below!"
                    )
                    await download_msg.update()
                    logger.info(f"Successfully downloaded model: {selected_model}")

                except Exception as e:
                    logger.error(f"Failed to download model {selected_model}: {e}", exc_info=True)
                    download_msg.content = (
                        f"❌ **Download failed**\n\n"
                        f"Could not download **{selected_model}**: {str(e)}\n\n"
                        f"Please try:\n"
                        f"- Selecting a different model from the dropdown\n"
                        f"- Running `/models pull {selected_model}` manually\n"
                        f"- Checking your internet connection"
                    )
                    await download_msg.update()

                return  # Exit early since we handled the welcome message
        else:
            welcome_msg = (
                "Welcome! I'm your local LLM assistant.\n\n"
                "**No models found.** Pull a model to get started:\n\n"
                "Try: `/models browse` to see available models\n"
                "Then: `/models pull llama3` to download one\n\n"
                "💡 **Tips:**\n"
                "- Check the **left sidebar** to view and resume past conversations\n"
                "- Type `/exit` or `/quit` to exit the application"
            )
            logger.warning("No local models found, prompting user to pull models")
    except OllamaNotRunningError:
        welcome_msg = (
            "Welcome! I'm your local LLM assistant.\n\n"
            "**Ollama is not running.** Please start it:\n"
            "```bash\n"
            "ollama serve\n"
            "```\n\n"
            "💡 **Tips:**\n"
            "- Check the **left sidebar** to view and resume past conversations\n"
            "- Type `/exit` or `/quit` to exit the application"
        )
        logger.warning("Ollama is not running, displaying startup instructions")

    # Send welcome message with system action buttons
    logger.debug("Sending welcome message with system action buttons")
    actions = get_system_actions() + [get_model_management_button()]
    await cl.Message(content=welcome_msg, actions=actions).send()
    logger.info("Chat session initialization complete")


@cl.on_message
async def on_message(message: cl.Message) -> None:
    """
    Handle incoming user messages with streaming response.

    Converts chat history to Ollama format and streams the response.
    Also handles /models commands for model management and system commands for exit.
    Supports file uploads by extracting and including file content in the message.
    """
    content = message.content.strip()
    content_preview = content[:100] + "..." if len(content) > 100 else content
    logger.info(f"Received user message: {content_preview}")
    logger.debug(f"Message length: {len(content)} characters")

    # Handle file uploads
    if message.elements:
        logger.info(f"Message contains {len(message.elements)} file(s)")
        file_contents = []

        for element in message.elements:
            logger.debug(f"Processing file element: {element.name}, type: {element.mime}")
            try:
                # Read file content
                if hasattr(element, 'path'):
                    logger.debug(f"Reading file from path: {element.path}")
                    with open(element.path, encoding='utf-8', errors='ignore') as f:
                        file_content = f.read()
                        file_contents.append(f"\n\n**File: {element.name}**\n```\n{file_content}\n```\n")
                        logger.info(f"Successfully read file: {element.name} ({len(file_content)} chars)")
                elif hasattr(element, 'content'):
                    # Some elements might have content directly
                    file_content = element.content.decode('utf-8', errors='ignore') if isinstance(element.content, bytes) else str(element.content)
                    file_contents.append(f"\n\n**File: {element.name}**\n```\n{file_content}\n```\n")
                    logger.info(f"Successfully read file content: {element.name} ({len(file_content)} chars)")
            except Exception as e:
                logger.error(f"Error reading file {element.name}: {e}", exc_info=True)
                file_contents.append(f"\n\n**File: {element.name}** (Error reading file: {str(e)})\n")

        # Append file contents to message
        if file_contents:
            content += "\n\n---\n**Uploaded Files:**\n" + "".join(file_contents)
            logger.debug(f"Appended {len(file_contents)} file(s) to message content")
    else:
        logger.debug("No files attached to message")

    # Check for system commands (/exit, /quit)
    if content.lower() in {"/exit", "/quit"} or content.lower().startswith("/system"):
        logger.info(f"Routing to system command handler: {content}")
        await handle_system_command(content)
        return

    # Check for model management commands
    if content.startswith("/models"):
        logger.info(f"Routing to model management command: {content}")
        await handle_model_command(content)
        return

    # Get session state
    model = cl.user_session.get("model")
    params = cl.user_session.get("parameters")
    system_prompt = cl.user_session.get("system_prompt")
    history = cl.user_session.get("messages") or []
    logger.debug(f"Session state: model={model}, history_length={len(history)}, has_system_prompt={system_prompt is not None}")

    # Build message history in Ollama format
    messages: list[dict[str, str]] = []

    # Add system prompt if set
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
        logger.debug("Added system prompt to message history")

    # Add chat history
    for h in history:
        messages.append({"role": h["role"], "content": h["content"]})
    logger.debug(f"Built message history: {len(messages)} messages (including current)")

    # Add current user message (with file content if any)
    messages.append({"role": "user", "content": content})

    # Create placeholder message for streaming with system action buttons
    msg_out = cl.Message(content="", actions=get_system_actions() + [get_model_management_button()])
    await msg_out.send()
    logger.debug("Initiated streaming response with system actions")

    # Stream response
    try:
        logger.info(f"Starting chat stream for user message with model: {model}")
        chunk_count = 0
        async for chunk in chat_stream(messages, model, params):
            msg_out.content += chunk
            chunk_count += 1
            await msg_out.update()

        logger.info(f"Chat stream completed: {chunk_count} chunks received, {len(msg_out.content)} total chars")
        logger.debug(f"Response preview: {msg_out.content[:200]}...")

    except OllamaNotRunningError as e:
        logger.error(f"Ollama not running error: {e}")
        msg_out.content = f"**Error:** {str(e)}"
        await msg_out.update()
        return
    except Exception as e:
        logger.error(f"Error during chat stream: {e}", exc_info=True)
        msg_out.content = f"**Error:** {str(e)}"
        await msg_out.update()
        return

    # Save to history (with file content included)
    history.append({"role": "user", "content": content})
    history.append({"role": "assistant", "content": msg_out.content})
    cl.user_session.set("messages", history)
    logger.debug(f"Saved to history: new history length = {len(history)}")

    # Auto-save session to disk using Chainlit's thread_id
    thread_id = cl.context.session.thread_id
    if thread_id:
        try:
            logger.info(f"Auto-saving session {thread_id} with {len(history)} messages")

            # Convert history dicts to ChatMessage objects
            chat_messages = [
                ChatMessage(role=msg["role"], content=msg["content"]) for msg in history
            ]

            # Save session with current state
            save_session(
                session_id=thread_id,
                model_name=model,
                messages=chat_messages,
                parameters=params,
                system_prompt=system_prompt,
            )
            logger.info(f"✓ Auto-saved thread {thread_id} successfully")
        except Exception as e:
            logger.error(f"Failed to auto-save thread {thread_id}: {e}", exc_info=True)
            # Don't show error to user, just log it
    else:
        logger.warning("No thread_id found in context, skipping auto-save")

    logger.info("Message processing complete")
