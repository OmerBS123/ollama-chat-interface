"""
Chat profiles for model selection.

Provides a dynamic dropdown of all available Ollama models (local + cloud)
that appears near the chat input area.
"""

import logging

import chainlit as cl
from chainlit.types import ChatProfile

from ..services.model_manager import list_cloud_models
from ..services.ollama_service import OllamaNotRunningError, list_local_models

logger = logging.getLogger(__name__)


@cl.set_chat_profiles
async def chat_profiles() -> list[ChatProfile]:
    """
    Create chat profiles for each available Ollama model.

    Returns a list of ChatProfile objects representing:
    - All local models (already downloaded)
    - Popular cloud models (available for download)

    Each profile shows model name, family, and size information.
    """
    logger.info("Building chat profiles for model selection")
    profiles: list[ChatProfile] = []

    # Get local models
    try:
        logger.debug("Fetching local models for chat profiles")
        local_models = list_local_models()

        if local_models:
            logger.info(f"Found {len(local_models)} local models")

            for model in local_models:
                # Skip embedding models
                if "embed" in model.name.lower():
                    logger.debug(f"Skipping embedding model: {model.name}")
                    continue

                # Extract model info from ModelInfo object
                model_name = model.name
                # ModelInfo has family as direct attribute (not nested under details)
                model_family = getattr(model, "family", None)
                # ModelInfo.size is in bytes, convert to MB for display
                model_size_bytes = getattr(model, "size", None)
                model_size_str = (
                    f"{model_size_bytes / (1024 * 1024):.1f}MB" if model_size_bytes else None
                )

                # Create description
                description_parts = [f"**{model_name}**"]
                if model_family:
                    description_parts.append(f"Family: {model_family}")
                if model_size_str:
                    description_parts.append(f"Size: {model_size_str}")

                description_parts.append("✅ Downloaded")

                markdown_desc = " • ".join(description_parts)

                profiles.append(
                    ChatProfile(
                        name=model_name,
                        markdown_description=markdown_desc,
                        icon="🦙",  # Llama icon for local models
                    )
                )
                logger.debug(f"Added chat profile: {model_name}")

        else:
            logger.warning("No local models found")

    except OllamaNotRunningError as e:
        logger.error(f"Ollama not running: {e}")
        # Add a placeholder profile
        profiles.append(
            ChatProfile(
                name="ollama-offline",
                markdown_description="⚠️ **Ollama is not running** - Start Ollama to see models",
                icon="⚠️",
            )
        )

    except Exception as e:
        logger.error(f"Error fetching local models: {e}", exc_info=True)

    # Get popular cloud models (not yet downloaded)
    try:
        logger.debug("Fetching cloud models for chat profiles")
        cloud_models = list_cloud_models()

        # Filter out models that are already downloaded
        local_names = {p.name for p in profiles}
        available_cloud = [m for m in cloud_models if m.name not in local_names]

        # Add ALL popular cloud models (removed limit)
        popular_models = available_cloud

        for model in popular_models:
            model_name = model.name  # Access as attribute, not dict
            # Build description from available fields (no "description" in ModelInfo)
            description = f"**{model_name}** • Available to download • ⬇️ Not Downloaded"

            profiles.append(
                ChatProfile(
                    name=model_name,
                    markdown_description=description,
                    icon="☁️",  # Cloud icon
                )
            )
            logger.debug(f"Added cloud model profile: {model_name}")

        if popular_models:
            logger.info(f"Added {len(popular_models)} cloud model profiles")

    except Exception as e:
        logger.error(f"Error fetching cloud models: {e}", exc_info=True)

    # If no profiles were created, add a default
    if not profiles:
        logger.warning("No profiles available, adding default profile")
        profiles.append(
            ChatProfile(
                name="llama3",
                markdown_description=(
                    "**llama3** • Default model • Use `/models pull llama3` to download"
                ),
                icon="🦙",
            )
        )

    logger.info(f"Created {len(profiles)} chat profiles")
    return profiles
