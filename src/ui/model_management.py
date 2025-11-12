"""
Model management UI handlers for Chainlit.

Provides commands for browsing, pulling, and deleting models directly from the chat interface.
"""

import logging

import chainlit as cl

from ..services.model_manager import filter_models, list_cloud_models
from ..services.ollama_service import (
    OllamaNotRunningError,
    delete_model,
    list_local_models,
    pull_model,
)

logger = logging.getLogger(__name__)


async def handle_model_command(command: str) -> None:
    """
    Parse and route /models commands.

    Supported commands:
    - /models list                  - List all local models
    - /models browse [pattern]      - Browse cloud models (with optional regex filter)
    - /models pull <name>           - Pull a model from Ollama Hub
    - /models delete <name>         - Delete a local model
    - /models search <pattern>      - Search both local and cloud with regex
    - /models help                  - Show help message

    Args:
        command: The full command string from user
    """
    logger.info(f"Model command received: {command}")
    parts = command.strip().split()
    logger.debug(f"Command parts: {parts}")

    if len(parts) < 2:
        logger.debug("No action specified, showing help")
        await show_models_help()
        return

    action = parts[1].lower()
    logger.debug(f"Action: {action}")

    if action == "list":
        logger.info("Handling 'list' command")
        await list_local_models_ui()
    elif action == "browse":
        pattern = parts[2] if len(parts) > 2 else ""
        logger.info(f"Handling 'browse' command with pattern: '{pattern}'")
        await browse_cloud_models_ui(pattern)
    elif action == "pull":
        if len(parts) < 3:
            logger.warning("Pull command missing model name")
            await cl.Message(content="**Usage:** `/models pull <model_name>`").send()
            return
        model_name = parts[2]
        logger.info(f"Handling 'pull' command for model: {model_name}")
        await pull_model_ui(model_name)
    elif action == "delete":
        if len(parts) < 3:
            logger.warning("Delete command missing model name")
            await cl.Message(content="**Usage:** `/models delete <model_name>`").send()
            return
        model_name = parts[2]
        logger.info(f"Handling 'delete' command for model: {model_name}")
        await delete_model_ui(model_name)
    elif action == "search":
        if len(parts) < 3:
            logger.warning("Search command missing pattern")
            await cl.Message(content="**Usage:** `/models search <pattern>`").send()
            return
        pattern = parts[2]
        logger.info(f"Handling 'search' command with pattern: {pattern}")
        await search_models_ui(pattern)
    elif action == "help":
        logger.info("Handling 'help' command")
        await show_models_help()
    else:
        logger.warning(f"Unknown action '{action}', showing help")
        await show_models_help()


async def show_models_help() -> None:
    """Display model management help message."""
    help_text = """## 🦙 Model Management Commands

**List local models:**
```
/models list
```

**Browse cloud models:**
```
/models browse [filter]
```

**Pull a model:**
```
/models pull <model_name>
```

**Delete local model:**
```
/models delete <model_name>
```

**Search with regex:**
```
/models search <pattern>
```

**Show this help:**
```
/models help
```

---

### Examples

- `/models browse llama` - Browse models matching "llama"
- `/models pull llama3` - Download llama3 model
- `/models delete mistral` - Remove mistral model
- `/models search "llama.*3"` - Search for llama3 variants

---

💡 **Tip:** Pulling large models may take several minutes depending on your internet connection.
"""
    await cl.Message(content=help_text).send()


async def list_local_models_ui() -> None:
    """Display local models in formatted table."""
    logger.info("Listing local models for UI display")
    try:
        models = list_local_models()
        logger.debug(f"Retrieved {len(models)} local models")

        if not models:
            logger.info("No local models found, prompting user to pull")
            content = (
                "## Local Models\n\n"
                "No local models found. Use `/models browse` to find and pull models.\n\n"
                "**Example:**\n"
                "```\n"
                "/models browse\n"
                "/models pull llama3\n"
                "```"
            )
            await cl.Message(content=content).send()
            return

        # Format as markdown table
        content = "## 📦 Local Models\n\n"
        content += "| Model Name | Size | Family |\n"
        content += "|------------|------|--------|\n"

        for m in models:
            size_str = f"{m.size / (1024**3):.2f} GB" if m.size else "N/A"
            family = m.family or "N/A"
            content += f"| `{m.name}` | {size_str} | {family} |\n"

        content += f"\n**Total:** {len(models)} model{'s' if len(models) != 1 else ''}"
        content += "\n\n💡 To delete a model: `/models delete <model_name>`"

        logger.info(f"Displaying {len(models)} models to user")
        await cl.Message(content=content).send()

    except OllamaNotRunningError as e:
        logger.error(f"Ollama not running: {e}")
        await cl.Message(content=f"**Error:** {str(e)}").send()


async def browse_cloud_models_ui(pattern: str = "") -> None:
    """
    Display cloud models with optional regex filtering.

    Args:
        pattern: Optional regex pattern to filter models
    """
    try:
        cloud_models = list_cloud_models()

        if not cloud_models:
            content = (
                "## ☁️ Cloud Models\n\n"
                "Could not fetch cloud models. This may be due to:\n"
                "- No internet connection\n"
                "- Missing OLLAMA_API_KEY in .env file\n"
                "- Ollama Hub API is down\n\n"
                "You can still pull models directly if you know the name:\n"
                "```\n"
                "/models pull llama3\n"
                "```"
            )
            await cl.Message(content=content).send()
            return

        # Apply filter if provided
        if pattern:
            cloud_models = filter_models(cloud_models, pattern)
            title = f"☁️ Cloud Models (filtered: `{pattern}`)"
        else:
            title = "☁️ Cloud Models"

        if not cloud_models:
            await cl.Message(
                content=f"No models match pattern: `{pattern}`\n\n"
                f"Try a different pattern or browse all: `/models browse`"
            ).send()
            return

        # Show first 20 models to avoid overwhelming the UI
        display_models = cloud_models[:20]

        content = f"## {title}\n\n"
        content += "**Available models:**\n\n"

        for m in display_models:
            content += f"- `{m.name}`\n"

        if len(cloud_models) > 20:
            content += (
                f"\n_Showing 20 of {len(cloud_models)} models. Use regex to narrow results._\n"
            )

        content += "\n\n**To pull a model:** `/models pull <model_name>`"
        content += "\n**Example:** `/models pull llama3`"

        await cl.Message(content=content).send()

    except Exception as e:
        await cl.Message(content=f"**Error browsing models:** {str(e)}").send()


async def pull_model_ui(model_name: str) -> None:
    """
    Pull a model from Ollama Hub with progress updates.

    Args:
        model_name: Name of the model to pull (e.g., "llama3", "mistral")
    """
    logger.info(f"User initiated pull for model: {model_name}")

    # Create progress message
    msg = cl.Message(
        content=f"🔄 Pulling model **{model_name}**...\n\n"
        f"This may take several minutes depending on model size and your connection.\n\n"
        f"_Please wait..._"
    )
    await msg.send()
    logger.debug("Sent progress message to user")

    try:
        logger.debug(f"Starting model pull operation for {model_name}")
        # Pull the model (blocking operation wrapped in async)
        await pull_model(model_name)

        logger.info(f"Successfully pulled model: {model_name}")
        msg.content = (
            f"✅ Successfully pulled model **{model_name}**!\n\n"
            f"You can now select it in the settings sidebar or use it directly.\n\n"
            f"To verify: `/models list`"
        )
        await msg.update()

    except OllamaNotRunningError as e:
        logger.error(f"Ollama not running while pulling {model_name}: {e}")
        msg.content = f"**Error:** {str(e)}"
        await msg.update()
    except Exception as e:
        logger.error(f"Failed to pull model {model_name}: {e}", exc_info=True)
        msg.content = (
            f"❌ Failed to pull model **{model_name}**\n\n"
            f"**Error:** {str(e)}\n\n"
            f"Make sure:\n"
            f"- Ollama is running (`ollama serve`)\n"
            f"- Model name is correct\n"
            f"- You have internet connection"
        )
        await msg.update()


async def delete_model_ui(model_name: str) -> None:
    """
    Delete a local model.

    Args:
        model_name: Exact name of the model to delete
    """
    logger.info(f"User initiated delete for model: {model_name}")

    try:
        # Check if model exists
        logger.debug("Checking if model exists locally")
        local_models = list_local_models()
        model_names = [m.name for m in local_models]
        logger.debug(f"Found {len(model_names)} local models")

        if model_name not in model_names:
            logger.warning(f"Model {model_name} not found locally")
            content = f"Model **{model_name}** not found locally.\n\nAvailable models:\n"
            for name in model_names:
                content += f"- `{name}`\n"
            content += "\nUse `/models list` to see all local models."
            await cl.Message(content=content).send()
            return

        # Delete the model
        logger.debug(f"Deleting model: {model_name}")
        delete_model(model_name)

        logger.info(f"Successfully deleted model: {model_name}")
        await cl.Message(
            content=f"✅ Deleted model **{model_name}**\n\nTo verify: `/models list`"
        ).send()

    except OllamaNotRunningError as e:
        logger.error(f"Ollama not running while deleting {model_name}: {e}")
        await cl.Message(content=f"**Error:** {str(e)}").send()
    except Exception as e:
        logger.error(f"Failed to delete model {model_name}: {e}", exc_info=True)
        await cl.Message(
            content=f"❌ Failed to delete model **{model_name}**\n\n**Error:** {str(e)}"
        ).send()


async def search_models_ui(pattern: str) -> None:
    """
    Search both local and cloud models with regex pattern.

    Args:
        pattern: Regex pattern to search for
    """
    try:
        # Get both local and cloud models
        local_models = list_local_models()
        cloud_models = list_cloud_models()

        # Filter both lists
        filtered_local = filter_models(local_models, pattern)
        filtered_cloud = filter_models(cloud_models, pattern)

        content = f"## 🔍 Search Results: `{pattern}`\n\n"

        # Local results
        content += f"### 📦 Local Models ({len(filtered_local)})\n"
        if filtered_local:
            for m in filtered_local:
                size_str = f" ({m.size / (1024**3):.2f} GB)" if m.size else ""
                content += f"- `{m.name}`{size_str}\n"
        else:
            content += "_No matches_\n"

        # Cloud results (show first 10)
        content += f"\n### ☁️ Cloud Models ({len(filtered_cloud)})\n"
        if filtered_cloud:
            for m in filtered_cloud[:10]:
                content += f"- `{m.name}`\n"
            if len(filtered_cloud) > 10:
                content += f"\n_...and {len(filtered_cloud) - 10} more_\n"
        else:
            content += "_No matches_\n"

        content += "\n\n**To pull a model:** `/models pull <model_name>`"

        await cl.Message(content=content).send()

    except Exception as e:
        await cl.Message(content=f"**Error searching models:** {str(e)}").send()
