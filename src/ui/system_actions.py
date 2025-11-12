"""
System action handlers for Chainlit UI.

Provides commands and action buttons for system operations like graceful application exit.
"""

import logging

import chainlit as cl

from ..services.system_service import shutdown_app, stop_ollama_daemon

logger = logging.getLogger(__name__)


async def handle_system_command(command: str) -> None:
    """
    Parse and route system commands.

    Supported commands:
    - /exit, /quit          - Exit the application
    - /system help          - Show system commands help

    Args:
        command: The full command string from user
    """
    logger.info(f"System command received: {command}")
    cmd = command.strip().lower()
    logger.debug(f"Normalized command: {cmd}")

    # Handle exit/quit commands
    if cmd in {"/exit", "/quit"}:
        logger.info("Handling exit/quit command")
        await exit_app()
    elif cmd in {"/system", "/system help"}:
        logger.info("Handling system help command")
        await show_system_help()
    else:
        logger.warning(f"Unknown system command: {cmd}, showing help")
        await show_system_help()


async def show_system_help() -> None:
    """Display system management help message."""
    logger.debug("Displaying system help message")
    help_text = """## ⚙️ System Commands

**Exit the application:**
```
/exit
/quit
```

**Show this help:**
```
/system help
```

---

### Notes

- Exiting will gracefully shut down the Chainlit server
- All operations are logged for audit purposes

"""
    await cl.Message(content=help_text).send()
    logger.debug("System help message sent")


async def exit_app() -> None:
    """Exit the application gracefully."""
    logger.info("Application exit initiated by user")
    await cl.Message(
        content="👋 **Application shut down successfully!**\n\n"
                "The Chainlit server has stopped.\n\n"
                "**You can now close this browser tab.**"
    ).send()
    logger.debug("Goodbye message sent, initiating shutdown with 1s delay")
    await shutdown_app(delay_seconds=1.0)
    logger.info("Shutdown initiated")


@cl.action_callback("exit_app")
async def on_exit_action(action: cl.Action) -> None:
    """
    Handle Exit App button click.

    Gracefully shuts down the Chainlit application.
    """
    logger.info("Exit App button clicked")
    await exit_app()


@cl.action_callback("stop_ollama_and_exit")
async def on_stop_ollama_action(action: cl.Action) -> None:
    """
    Handle Stop Ollama & Exit button click.

    Stops the Ollama daemon and then exits the application.
    """
    logger.info("Stop Ollama & Exit button clicked")

    # Stop Ollama daemon
    success, message = stop_ollama_daemon()
    await cl.Message(content=message).send()

    if success:
        logger.info("Ollama stopped successfully, proceeding with app shutdown")
    else:
        logger.warning("Ollama stop failed or not running, proceeding with app shutdown anyway")

    # Exit regardless of Ollama stop result
    await cl.Message(
        content="👋 **Shutting down...**\n\n"
                "The Chainlit server has stopped.\n\n"
                "**You can now close this browser tab.**"
    ).send()
    logger.debug("Goodbye message sent, initiating shutdown with 1s delay")
    await shutdown_app(delay_seconds=1.0)
    logger.info("Shutdown initiated")


def get_system_actions() -> list[cl.Action]:
    """
    Get list of system action buttons.

    Returns:
        List of Action objects for system operations (stop Ollama & exit)
    """
    logger.debug("Creating system action buttons")
    return [
        cl.Action(
            name="stop_ollama_and_exit",
            label="🛑 Stop Ollama & Exit",
            description="Stop Ollama daemon and exit the application",
            payload={},
        ),
    ]
