"""Application configuration module.

Args:
    settings (Settings): The settings for the application
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Model for application settings.

    Any default settings will be overwritten by environment variables.
    """

    app_title: str
    app_description: str
    db_url: str
    db_sqlite: bool

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


def get_settings() -> Settings:
    """Get the application settings."""

    return Settings(
        app_title="Bulletinator",
        app_description="A project management and collaboration app",
        db_url="sqlite:///backend/database/development.db",
        db_sqlite=True,
    )

settings = get_settings()