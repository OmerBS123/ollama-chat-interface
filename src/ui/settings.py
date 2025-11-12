"""
Settings UI for model parameters and configuration.

Handles settings updates for temperature, top_p, max_tokens, model selection,
and system prompt.
"""

import logging
from typing import Any

import chainlit as cl
from chainlit.input_widget import NumberInput, Slider, TextInput

from ..models.schemas import ModelParameters

logger = logging.getLogger(__name__)


@cl.on_settings_update
async def on_settings_update(settings: dict[str, Any]) -> None:
    """
    Handle settings changes from the UI.

    Updates parameters and system prompt in user session.
    Model selection is now handled via chat profiles dropdown.
    """
    logger.info("Settings update received")
    logger.debug(f"Settings: {settings}")

    # Update model parameters
    # Convert 0 to None for max_tokens (0 = unlimited)
    max_tokens_value = settings.get("max_tokens")
    if max_tokens_value == 0:
        max_tokens_value = None
        logger.debug("Converted max_tokens from 0 to None (unlimited)")

    logger.debug(
        f"Settings values received: temp={settings.get('temperature')}, "
        f"top_p={settings.get('top_p')}, max_tokens_input={settings.get('max_tokens')} "
        f"(converted to {max_tokens_value})"
    )

    params = ModelParameters(
        temperature=settings.get("temperature", 0.7),
        top_p=settings.get("top_p", 0.9),
        max_tokens=max_tokens_value,
    )
    cl.user_session.set("parameters", params)
    logger.debug(
        f"Updated parameters: temp={params.temperature}, "
        f"top_p={params.top_p}, max_tokens={params.max_tokens}"
    )

    # Update system prompt
    if "system_prompt" in settings:
        system_prompt = (settings["system_prompt"] or "").strip()
        cl.user_session.set("system_prompt", system_prompt if system_prompt else None)
        if system_prompt:
            logger.info(f"System prompt set: {system_prompt[:50]}...")
        else:
            logger.info("System prompt cleared")

    # Notify user
    await cl.Message(content="⚙️ Settings updated successfully!").send()
    logger.debug("Settings update complete")


def get_settings_config(
    current_model: str,
    current_params: ModelParameters,
    current_system_prompt: str | None = None,
) -> list[cl.input_widget.InputWidget]:
    """
    Get Chainlit settings configuration with current session values.

    Includes parameters and system prompt controls.
    Model selection is handled via chat profiles dropdown (top-left).

    Args:
        current_model: Current model name from session (unused, kept for compatibility)
        current_params: Current model parameters from session
        current_system_prompt: Current system prompt from session (if any)

    Returns:
        List of Chainlit input widgets for settings.
    """
    logger.info(
        f"Building settings config - temp={current_params.temperature}, "
        f"top_p={current_params.top_p}, max_tokens={current_params.max_tokens}"
    )
    logger.debug(f"System prompt provided: {bool(current_system_prompt)}")

    # Create settings widgets (NO model selector - use chat profiles instead)
    logger.debug("Creating settings widgets without model selector")
    widgets = [
        Slider(
            id="temperature",
            label="Temperature",
            min=0.0,
            max=2.0,
            step=0.1,
            initial=current_params.temperature,
            tooltip="Controls randomness: 0 = deterministic, 2 = very creative",
        ),
        Slider(
            id="top_p",
            label="Top P",
            min=0.0,
            max=1.0,
            step=0.05,
            initial=current_params.top_p,
            tooltip="Nucleus sampling: higher = more diverse responses",
        ),
        NumberInput(
            id="max_tokens",
            label="Max Tokens",
            initial=current_params.max_tokens or 0,
            tooltip="Maximum tokens to generate (0 = unlimited)",
        ),
        TextInput(
            id="system_prompt",
            label="System Prompt",
            initial=current_system_prompt or "",
            tooltip="Custom system prompt to guide the assistant's behavior",
        ),
    ]

    logger.info(f"Settings configuration built successfully with {len(widgets)} widgets")
    logger.debug(
        f"Widget initial values: "
        f"temp={current_params.temperature}, top_p={current_params.top_p}, "
        f"max_tokens={current_params.max_tokens or 0}, "
        f"has_system_prompt={bool(current_system_prompt)}"
    )

    return widgets
