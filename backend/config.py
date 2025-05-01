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
    app_domain: str

    db_url: str
    db_sqlite: bool
    assets_folder_path: str

    jwt_algorithm: str
    jwt_access_cookie_key: str
    jwt_refresh_cookie_key: str
    jwt_access_duration: int
    jwt_refresh_duration: int
    jwt_secret_key: str = "jwt-secret-key-dev"
    cookie_max_age: int

    email_verification_duration: int
    editor_invitation_duration: int
    smtp_host: str
    smtp_port: int
    smtp_sender: str
    smtp_login: str
    smtp_password: str

    stripe_secret_key: str
    stripe_webhook_secret: str

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
        assets_folder_path="./assets/",

        jwt_algorithm="HS256",
        jwt_access_cookie_key="bulletinator_access_token",
        jwt_refresh_cookie_key="bulletinator_refresh_token",
        jwt_access_duration=900,
        jwt_refresh_duration=3600*24*14,
        app_domain="http://127.0.0.1",
        cookie_max_age=3600*24*14,

        email_verification_duration=3600*24, # Should expire after 24 hours
        editor_invitation_duration=3600*24*7, # Should expire after 7 days

        static_path=os.path.join(os.getcwd(), 'static'),
        media_img_max_bytes=1024*1024,
    )

settings = get_settings()