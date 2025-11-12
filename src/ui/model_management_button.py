"""
Model management button and action handlers.

Provides a button to manage downloaded models (view, delete).
"""

import logging

import chainlit as cl

from ..services.ollama_service import (
    OllamaNotRunningError,
    delete_model,
    list_local_models,
)

logger = logging.getLogger(__name__)


def get_model_management_button() -> cl.Action:
    """
    Create the 'Manage Models' action button.

    Returns:
        Action button for model management
    """
    return cl.Action(
        name="manage_models",
        label="🗑️ Manage Models",
        description="View and delete downloaded models",
        payload={},
    )


@cl.action_callback("manage_models")
async def on_manage_models_action(action: cl.Action) -> None:
    """
    Handle 'Manage Models' button click.

    Shows all local models with delete buttons for each.
    """
    logger.info("Manage models action clicked")

    try:
        # Get local models
        logger.debug("Fetching local models for management")
        models = list_local_models()

        if not models:
            logger.info("No local models found")
            await cl.Message(
                content=(
                    "**No models found locally.**\n\nUse `/models pull <name>` to download models."
                ),
            ).send()
            return

        logger.info(f"Found {len(models)} local models")

        # Build model list with delete actions - one model per line
        model_list = "**📦 Downloaded Models:**\n\n"
        delete_actions = []

        for model in models:
            model_name = model.name
            model_family = getattr(model, "family", None)
            model_size_bytes = getattr(model, "size", None)
            model_size_str = (
                f"{model_size_bytes / (1024**3):.2f} GB" if model_size_bytes else "unknown size"
            )

            # Display one model per line for better readability
            model_list += f"**{model_name}**\n"
            if model_family:
                model_list += f"Family: {model_family} • Size: {model_size_str}\n"
            else:
                model_list += f"Size: {model_size_str}\n"
            model_list += "\n"

            # Create delete action for this model
            delete_actions.append(
                cl.Action(
                    name="delete_model",  # Fixed name for all models
                    label=f"🗑️ Delete {model_name}",
                    description=f"Remove {model_name} from local storage",
                    payload={"model_name": model_name},
                )
            )

        model_list += "💡 **Tip:** Click a delete button to remove a model.\n"
        model_list += "⚠️ **Warning:** Deleting a model will refresh your current chat."

        # Send message with delete actions
        await cl.Message(content=model_list, actions=delete_actions).send()
        logger.debug(f"Sent model list with {len(delete_actions)} delete actions")

    except OllamaNotRunningError as e:
        logger.error(f"Ollama not running: {e}")
        await cl.Message(
            content=(
                "**⚠️ Ollama is not running.**\n\nPlease start Ollama:\n```bash\nollama serve\n```"
            ),
        ).send()
    except Exception as e:
        logger.error(f"Error managing models: {e}", exc_info=True)
        await cl.Message(content=f"**Error:** {str(e)}").send()


@cl.action_callback("delete_model")
async def on_delete_model_action(action: cl.Action) -> None:
    """
    Handle model deletion with confirmation.

    Args:
        action: Action containing model name to delete in payload
    """
    model_name = action.payload.get("model_name")
    logger.info(f"Delete action clicked for model: {model_name}")

    try:
        # Ask for confirmation and capture the response inline
        logger.debug(f"Showing confirmation dialog for {model_name}")
        res = await cl.AskActionMessage(
            content=f"**⚠️ Warning: This will refresh your current chat**\n\n"
            f"Are you sure you want to delete model `{model_name}`?\n\n"
            f"This will permanently remove the model from local storage.\n\n"
            f"You can re-download it later with `/models pull {model_name}`.",
            actions=[
                cl.Action(
                    name="confirm_delete",
                    label="✅ Yes, Delete",
                    payload={"model_name": model_name},
                ),
                cl.Action(
                    name="cancel_delete",
                    label="❌ Cancel",
                    payload={},
                ),
            ],
        ).send()

        logger.debug(f"User response received: {res}")

        # Handle the response inline
        if res and res.get("name") == "confirm_delete":
            logger.info(f"User confirmed deletion of {model_name}")

            # Show deletion progress
            status_msg = cl.Message(content=f"🗑️ **Deleting model `{model_name}`...**")
            await status_msg.send()

            try:
                # Delete the model
                logger.debug(f"Calling delete_model() for {model_name}")
                delete_model(model_name)
                logger.info(f"Successfully deleted model: {model_name}")

                # Show success message
                status_msg.content = (
                    f"✅ **Model `{model_name}` deleted successfully!**\n\n"
                    f"The model has been removed from local storage.\n\n"
                    f"💡 **Tip:** Refresh your browser (F5) or continue "
                    f"chatting with another model."
                )
                await status_msg.update()
                logger.info(f"Model {model_name} deleted successfully")

            except OllamaNotRunningError as e:
                logger.error(f"Ollama not running during deletion: {e}")
                status_msg.content = (
                    "**⚠️ Ollama is not running.**\n\nPlease start Ollama and try again."
                )
                await status_msg.update()
            except Exception as e:
                logger.error(f"Failed to delete model {model_name}: {e}", exc_info=True)
                status_msg.content = (
                    f"❌ **Failed to delete `{model_name}`**\n\nError: {str(e)}\n\n"
                )
                await status_msg.update()

        elif res and res.get("name") == "cancel_delete":
            logger.info("User cancelled deletion")
            await cl.Message(content="❌ **Deletion cancelled.**").send()
        else:
            logger.warning(f"Unexpected response from confirmation dialog: {res}")

    except Exception as e:
        logger.error(f"Error in delete model action: {e}", exc_info=True)
        await cl.Message(content=f"**Error:** {str(e)}").send()
