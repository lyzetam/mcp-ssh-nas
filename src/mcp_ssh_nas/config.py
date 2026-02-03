"""Pydantic Settings configuration for SSH NAS MCP server."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """SSH NAS connection configuration.

    Reads from environment variables with NAS_ prefix or .env file.
    """

    host: str = Field(default="", description="NAS hostname or IP address")
    port: int = Field(default=22, description="SSH port")
    user: str = Field(default="", description="SSH username")
    password: str = Field(default="", description="SSH password")

    model_config = SettingsConfigDict(
        env_prefix="NAS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


def get_settings() -> Settings:
    """Get configuration from environment variables or .env file."""
    return Settings()
