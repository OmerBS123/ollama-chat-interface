"""
System service for application and Ollama daemon management.

Provides functions for gracefully shutting down the app and managing the Ollama daemon.
"""

import asyncio
import logging
import os
import subprocess
import sys

# Initialize logger
logger = logging.getLogger(__name__)


async def shutdown_app(delay_seconds: float = 1.0) -> None:
    """
    Gracefully shutdown the Chainlit application.

    Args:
        delay_seconds: Time to wait before shutting down (allows messages to be sent)
    """
    logger.info("Application shutdown requested")
    logger.debug(f"Shutdown delay: {delay_seconds} seconds")

    # Wait for any pending operations to complete
    await asyncio.sleep(delay_seconds)

    logger.info("Shutting down application now")

    # Exit with success code
    # Using os._exit(0) instead of sys.exit() for immediate shutdown
    # This is necessary because sys.exit() can be caught by exception handlers
    os._exit(0)


def get_ollama_pid() -> int | None:
    """
    Get the process ID of the Ollama daemon running on port 11434.

    Returns:
        Process ID if found, None otherwise
    """
    try:
        # Use lsof to find process listening on port 11434
        result = subprocess.run(
            ["lsof", "-ti", ":11434"],
            capture_output=True,
            text=True,
            check=False,  # Don't raise exception if command fails
        )

        if result.returncode == 0 and result.stdout.strip():
            pid = int(result.stdout.strip())
            logger.debug(f"Found Ollama PID: {pid}")
            return pid

        logger.debug("No process found on port 11434")
        return None

    except (subprocess.SubprocessError, ValueError) as e:
        logger.error(f"Error getting Ollama PID: {e}")
        return None
    except FileNotFoundError:
        logger.warning("lsof command not found (not available on this system)")
        return None


def stop_ollama_daemon() -> tuple[bool, str]:
    """
    Stop the Ollama daemon process.

    Returns:
        Tuple of (success: bool, message: str)
    """
    logger.info("Attempting to stop Ollama daemon")

    # Check platform compatibility
    if sys.platform == "win32":
        logger.warning("Ollama stop is not supported on Windows")
        return False, "⚠️ Stopping Ollama is not supported on Windows. Please stop it manually."

    # Get Ollama process ID
    pid = get_ollama_pid()

    if pid is None:
        logger.info("Ollama daemon not found (not running or not on port 11434)")
        return False, "⚠️ Ollama daemon is not running on port 11434."

    try:
        # Send SIGTERM signal for graceful shutdown
        logger.info(f"Sending SIGTERM to Ollama process {pid}")
        subprocess.run(["kill", "-15", str(pid)], check=True)

        logger.info(f"Successfully stopped Ollama daemon (PID: {pid})")
        return True, f"✅ Ollama daemon stopped (PID: {pid})"

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to stop Ollama daemon: {e}")
        return False, f"❌ Failed to stop Ollama daemon: {e}"
    except Exception as e:
        logger.error(f"Unexpected error stopping Ollama: {e}", exc_info=True)
        return False, f"❌ Unexpected error: {e}"


def check_ollama_running() -> bool:
    """
    Check if Ollama daemon is currently running.

    Returns:
        True if running, False otherwise
    """
    pid = get_ollama_pid()
    return pid is not None
