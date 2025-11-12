"""
Model manager for cloud/local model management and filtering.

Handles listing cloud models from Ollama Hub, filtering models by regex,
and combining local and cloud model lists.
"""

import logging
import re

from ..models.schemas import ModelInfo

logger = logging.getLogger(__name__)

# URL for Ollama Cloud API
CLOUD_TAGS_URL = "https://ollama.com/api/tags"


def list_cloud_models() -> list[ModelInfo]:
    """
    List popular, verified models available from Ollama Hub.

    Returns a curated list of working Ollama models that can be pulled.
    These are real, tested models from ollama.com/library.

    Returns:
        List of ModelInfo objects for popular cloud models
    """
    logger.info("Getting popular Ollama Hub models (curated list)")

    # Curated list of popular, verified Ollama models
    # These are guaranteed to exist and be pullable from Ollama Hub
    popular_models = [
        "llama3.2",  # Latest Llama 3.2 (small, fast)
        "llama3.2:3b",  # Llama 3.2 3B parameters
        "mistral",  # Mistral 7B (excellent quality)
        "gemma2",  # Google's Gemma 2
        "qwen2.5",  # Alibaba's Qwen 2.5
        "phi3",  # Microsoft Phi-3 (small but capable)
        "codellama",  # Code-specialized Llama
        "deepseek-coder",  # Excellent for coding
        "llama3.1",  # Llama 3.1 (previous version)
        "mixtral",  # Mixtral 8x7B (powerful)
    ]

    model_infos = [ModelInfo(name=name) for name in popular_models]
    logger.info(f"Returning {len(model_infos)} popular cloud models")
    logger.debug(f"Cloud model names: {[m.name for m in model_infos]}")

    return model_infos


def filter_models(models: list[ModelInfo], pattern: str) -> list[ModelInfo]:
    """
    Filter models by regex pattern on name.

    CRITICAL: Uses re.IGNORECASE for user-friendly filtering.

    Args:
        models: List of ModelInfo objects
        pattern: Regex pattern string (e.g., "gpt", "llama.*3")

    Returns:
        Filtered list of ModelInfo objects matching the pattern
    """
    logger.debug(f"Filtering {len(models)} models with pattern: '{pattern}'")

    if not pattern:
        logger.debug("No pattern provided, returning all models")
        return models

    try:
        regex = re.compile(pattern, re.IGNORECASE)
        logger.debug(f"Compiled regex pattern: {regex.pattern} (flags: IGNORECASE)")

        filtered = [m for m in models if regex.search(m.name)]
        logger.info(f"Filter matched {len(filtered)}/{len(models)} models")
        matched_names = [m.name for m in filtered[:10]]
        ellipsis = "..." if len(filtered) > 10 else ""
        logger.debug(f"Matched models: {matched_names}{ellipsis}")

        return filtered

    except re.error as e:
        # Invalid regex - return all models
        logger.warning(f"Invalid regex pattern '{pattern}': {e}. Returning all models.")
        return models


def get_available_models(local_models: list[ModelInfo]) -> dict[str, list[ModelInfo]]:
    """
    Get available models from both local and cloud sources.

    Args:
        local_models: List of local ModelInfo objects

    Returns:
        Dictionary with 'local' and 'cloud' keys containing model lists
    """
    logger.info(f"Getting available models (local count: {len(local_models)})")
    logger.debug(f"Local models: {[m.name for m in local_models]}")

    cloud_models = list_cloud_models()
    logger.debug(f"Retrieved {len(cloud_models)} cloud models")

    result = {"local": local_models, "cloud": cloud_models}
    logger.info(f"Available models summary: {len(local_models)} local, {len(cloud_models)} cloud")

    return result
