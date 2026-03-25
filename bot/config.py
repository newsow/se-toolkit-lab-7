"""Configuration loading from environment variables.

This module uses pydantic-settings to load configuration from .env.bot.secret.
Secrets are never hardcoded in the codebase.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Bot configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file="../.env.bot.secret",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Telegram bot token
    bot_token: str = ""

    # LMS API configuration
    lms_api_base_url: str = "http://localhost:42002"
    lms_api_key: str = ""

    # LLM API configuration
    llm_api_model: str = "coder-model"
    llm_api_key: str = ""
    llm_api_base_url: str = ""


settings = Settings()
