"""
Ollama service wrapper.

Provides async interface for Ollama SDK operations including chat streaming,
model listing, pulling, and deletion.
"""

import asyncio
import logging
from collections.abc import AsyncGenerator
from typing import Any

import ollama
from ollama import ResponseError

from ..models.schemas import ModelInfo, ModelParameters

# Initialize logger
logger = logging.getLogger(__name__)


class OllamaNotRunningError(Exception):
    """Raised when Ollama daemon is not running."""

    pass


async def chat_stream(
    messages: list[dict[str, str]], model: str, params: ModelParameters
) -> AsyncGenerator[str]:
    """
    Stream chat responses from Ollama.

    Args:
        messages: List of messages in Ollama format [{"role": "...", "content": "..."}]
        model: Model name to use
        params: Model parameters

    Yields:
        Content chunks from the streaming response

    Raises:
        OllamaNotRunningError: If Ollama daemon is not running
    """
    logger.info(f"Starting chat stream with model: {model}")
    logger.debug(f"Parameters: temp={params.temperature}, top_p={params.top_p}, max_tokens={params.max_tokens}")
    logger.debug(f"Message count: {len(messages)}")

    # Log message history (truncate content for readability)
    for i, msg in enumerate(messages):
        content_preview = msg.get("content", "")[:100]
        if len(msg.get("content", "")) > 100:
            content_preview += "..."
        logger.debug(f"Message {i+1}: role={msg.get('role')}, content={content_preview}")

    try:
        # Build options dict for Ollama
        options: dict[str, Any] = {
            "temperature": params.temperature,
            "top_p": params.top_p,
        }

        # CRITICAL: Ollama uses 'num_predict' not 'max_tokens'
        if params.max_tokens:
            options["num_predict"] = params.max_tokens

        logger.debug(f"Chat options: {options}")
        logger.debug("Initiating streaming request to Ollama")

        # CRITICAL: ollama.chat() is sync and returns generator when stream=True
        chunk_count = 0
        total_chars = 0
        for chunk in ollama.chat(model=model, messages=messages, stream=True, options=options):
            # Each chunk has structure: {"message": {"content": "..."}}
            content = chunk.get("message", {}).get("content", "")
            if content:
                chunk_count += 1
                total_chars += len(content)
                logger.debug(f"Chunk {chunk_count}: {len(content)} chars")
                yield content

        logger.info(f"Chat stream completed: {chunk_count} chunks sent, {total_chars} total characters")

    except ResponseError as e:
        # Handle Ollama API errors (e.g., embedding models that don't support chat)
        if "does not support chat" in str(e):
            error_msg = (
                f"⚠️ **Error:** The model `{model}` is an embedding model and cannot be used for chat.\n\n"
                f"**Embedding models** are designed for generating text embeddings (vector representations), "
                f"not for conversational responses.\n\n"
                f"**Solution:** Please select a chat model from the settings, such as:\n"
                f"- llama3\n"
                f"- mistral\n"
                f"- gemma\n"
            )
            logger.error(f"Attempted to chat with embedding model: {model}")
            yield error_msg
        else:
            logger.error(f"Ollama API error: {e}", exc_info=True)
            yield f"**Error:** {str(e)}"
    except ConnectionError as e:
        logger.error(f"Ollama connection error: {e}")
        raise OllamaNotRunningError("Ollama is not running. Start it with: ollama serve") from e
    except Exception as e:
        logger.error(f"Chat stream error: {e}", exc_info=True)
        # Yield error message for display in chat
        yield f"**Error:** {str(e)}"


def list_local_models() -> list[ModelInfo]:
    """
    List all locally installed Ollama models.

    Returns:
        List of ModelInfo objects for each local model

    Raises:
        OllamaNotRunningError: If Ollama daemon is not running
    """
    logger.debug("Listing local Ollama models")
    try:
        logger.debug("Calling ollama.list() API")
        result = ollama.list()  # Returns: {"models": [...]}
        logger.debug(f"Received response from ollama.list(): {len(result.get('models', []))} models")

        models = result.get("models", [])

        # DEBUG: Log first model's structure (Pydantic object)
        if models:
            logger.debug(f"First model type: {type(models[0])}")
            logger.debug(f"First model: {models[0]}")
            # Try common attribute names
            logger.debug(f"Has 'name' attribute: {hasattr(models[0], 'name')}")
            logger.debug(f"Has 'model' attribute: {hasattr(models[0], 'model')}")

        # Convert to ModelInfo objects for type safety
        model_infos = []
        for i, m in enumerate(models):
            # Access Pydantic model attributes directly
            # Try 'model' attribute first (likely correct), fallback to 'name'
            model_name = None
            if hasattr(m, 'model') and m.model:
                model_name = m.model
                logger.debug(f"Model {i}: Using 'model' attribute = '{model_name}'")
            elif hasattr(m, 'name') and m.name:
                model_name = m.name
                logger.debug(f"Model {i}: Using 'name' attribute = '{model_name}'")
            else:
                model_name = str(m)  # Fallback to string representation
                logger.warning(f"Model {i}: Could not find name/model attribute, using string representation: {model_name}")

            # Access other attributes directly (not with .get())
            model_info = ModelInfo(
                name=model_name,
                size=getattr(m, 'size', None),
                modified_at=getattr(m, 'modified_at', None),
                digest=getattr(m, 'digest', None),
                family=getattr(getattr(m, 'details', None), 'family', None) if hasattr(m, 'details') else None,
            )
            logger.debug(f"Model {i}: Created ModelInfo with name='{model_info.name}'")
            model_infos.append(model_info)

        logger.info(f"Found {len(model_infos)} local models")
        # Log model details at debug level
        for model in model_infos:
            size_mb = f"{model.size / (1024*1024):.1f}MB" if model.size else "unknown size"
            logger.debug(f"Model: {model.name}, family={model.family}, size={size_mb}")

        return model_infos
    except ConnectionError as e:
        logger.error(f"Ollama connection error while listing models: {e}")
        raise OllamaNotRunningError("Ollama is not running. Start it with: ollama serve") from e


async def pull_model(name: str) -> None:
    """
    Pull a model from Ollama Hub to local storage.

    CRITICAL: ollama.pull() is blocking, so we wrap it in asyncio.to_thread()

    Args:
        name: Name of the model to pull (e.g., "llama3", "mistral")

    Raises:
        OllamaNotRunningError: If Ollama daemon is not running
    """
    logger.info(f"Pulling model: {name}")
    logger.debug("Running ollama.pull() in thread pool to avoid blocking")
    try:
        # Run blocking ollama.pull() in a thread pool
        logger.debug(f"Initiating pull request for model: {name}")
        await asyncio.to_thread(ollama.pull, name)
        logger.info(f"Successfully pulled model: {name}")
        logger.debug(f"Model {name} is now available locally")
    except ConnectionError as e:
        logger.error(f"Ollama connection error while pulling {name}: {e}")
        raise OllamaNotRunningError("Ollama is not running. Start it with: ollama serve") from e
    except Exception as e:
        logger.error(f"Failed to pull model {name}: {e}", exc_info=True)
        raise


async def pull_model_with_progress(name: str) -> AsyncGenerator[dict[str, Any]]:
    """
    Pull a model from Ollama Hub with live progress updates.

    Streams progress information as the model downloads, allowing
    the UI to show real-time download progress.

    Args:
        name: Name of the model to pull (e.g., "llama3", "mistral")

    Yields:
        Progress dictionaries with status, completed, and total bytes

    Raises:
        OllamaNotRunningError: If Ollama daemon is not running
    """
    logger.info(f"Pulling model with progress: {name}")

    try:
        # Pull with streaming enabled
        logger.debug(f"Initiating streaming pull for model: {name}")

        def _pull_stream():
            """Wrapper to run ollama.pull with stream=True in thread."""
            return ollama.pull(name, stream=True)

        # Run in thread pool since ollama.pull is blocking
        stream = await asyncio.to_thread(_pull_stream)

        # Stream progress updates
        for progress_dict in stream:
            logger.debug(f"Pull progress for {name}: {progress_dict}")
            yield progress_dict

        logger.info(f"Successfully pulled model: {name}")

    except ConnectionError as e:
        logger.error(f"Ollama connection error while pulling {name}: {e}")
        raise OllamaNotRunningError("Ollama is not running. Start it with: ollama serve") from e
    except Exception as e:
        logger.error(f"Failed to pull model {name}: {e}", exc_info=True)
        raise


def delete_model(name: str) -> None:
    """
    Delete a locally stored model.

    CRITICAL: Model name must exactly match the name from ollama.list()

    Args:
        name: Exact name of the model to delete

    Raises:
        OllamaNotRunningError: If Ollama daemon is not running
    """
    logger.info(f"Deleting model: {name}")
    logger.debug("Model name must exactly match the name from ollama.list()")
    try:
        logger.debug(f"Calling ollama.delete() for model: {name}")
        ollama.delete(name)
        logger.info(f"Successfully deleted model: {name}")
        logger.debug(f"Model {name} has been removed from local storage")
    except ConnectionError as e:
        logger.error(f"Ollama connection error while deleting {name}: {e}")
        raise OllamaNotRunningError("Ollama is not running. Start it with: ollama serve") from e
    except Exception as e:
        logger.error(f"Failed to delete model {name}: {e}", exc_info=True)
        raise
