"""
Configuration settings for CanaryFile Engine listener server.
Supports environment variables and YAML config files.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class WebhookConfig(BaseModel):
    """Webhook notification settings."""
    enabled: bool = False
    url: Optional[str] = None
    platform: str = "generic"  # generic, slack, discord, teams
    timeout_seconds: float = 5.0


class Settings(BaseSettings):
    """Application settings with environment variable fallback."""
    
    app_name: str = "CanaryFile Engine Listener"
    app_version: str = "0.1.0"
    debug: bool = False
    
    host: str = "0.0.0.0"
    port: int = 8000
    
    # SQLite Database path
    db_path: str = "canary_tokens.db"
    
    # Webhook Alerting
    webhook_enabled: bool = False
    webhook_url: Optional[str] = None
    webhook_platform: str = "generic"
    
    # Response settings for canary endpoint
    # Return 1x1 transparent GIF (default) or 204 No Content
    return_gif: bool = True

    # Security & Rate Limiting
    api_key: Optional[str] = None
    rate_limit_per_minute: int = 60

    model_config = SettingsConfigDict(
        env_prefix="CANARY_",
        env_file=".env",
        extra="ignore"
    )


# Singleton instance
settings = Settings()
