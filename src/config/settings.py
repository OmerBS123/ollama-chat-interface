"""
Configuration and settings module.

Loads environment variables and provides defaults for all settings.
"""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Settings:
    """Application settings from environment variables."""

    def __init__(self) -> None:
        # Ollama Configuration
        self.ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_api_key: str | None = os.getenv("OLLAMA_API_KEY")

        # Application Settings
        self.default_model: str = os.getenv("DEFAULT_MODEL", "llama3")
        self.default_temperature: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
        self.default_top_p: float = float(os.getenv("DEFAULT_TOP_P", "0.9"))
        self.default_max_tokens: int | None = (
            int(os.getenv("DEFAULT_MAX_TOKENS")) if os.getenv("DEFAULT_MAX_TOKENS") else None
        )

        # Logging Configuration
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.log_dir: str = os.getenv("LOG_DIR", "logs")

        # Chat History
        session_dir = os.getenv("SESSION_DATA_DIR", "data/sessions")
        self.session_data_dir: Path = Path(session_dir)

        # Ensure session directory exists
        self.session_data_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
