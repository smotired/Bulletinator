"""Application configuration module.

Args:
    settings (Settings): The settings for the application
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    """Model for application settings.

    Any default settings will be overwritten by environment variables.
    """

    app_title: str
    app_description: str

    db_url: str
    db_sqlite: bool
    favicon_path: str

    jwt_algorithm: str
    jwt_access_cookie_key: str
    jwt_refresh_cookie_key: str
    jwt_access_duration: int
    jwt_refresh_duration: int
    jwt_issuer: str
    jwt_secret_key: str = "jwt-secret-key-dev"
    cookie_max_age: int

    static_path: str
    media_img_max_bytes: int

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


def get_settings() -> Settings:
    """Get the application settings."""

    return Settings(
        app_title="Bulletinator",
        app_description="A project management and collaboration app",

        db_url="sqlite:///database/development.db",
        db_sqlite=True,
        favicon_path="favicon.ico",

        jwt_algorithm="HS256",
        jwt_access_cookie_key="bulletinator_access_token",
        jwt_refresh_cookie_key="bulletinator_refresh_token",
        jwt_access_duration=900,
        jwt_refresh_duration=3600*24*14,
        jwt_issuer="http://127.0.0.1",
        cookie_max_age=3600*24*14,

        static_path=os.path.join(os.getcwd(), 'static'),
        media_img_max_bytes=1024*1024,
    )

settings = get_settings()