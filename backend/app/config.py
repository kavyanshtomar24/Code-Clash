"""
Application configuration loaded from environment variables.

Uses Pydantic Settings to validate and type-check all configuration
values at startup, failing fast on misconfiguration.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import JUDGE_QUEUE_KEY


class Settings(BaseSettings):
    """Central application settings sourced from .env file and environment."""

    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CODEFORCES_API_URL: str = "https://codeforces.com/api"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    DEBUG: bool = True

    # Admin usernames (comma-separated in env) may create problems
    ADMIN_USERNAMES: list[str] = ["admin"]

    JUDGE_QUEUE_KEY: str = JUDGE_QUEUE_KEY
    JUDGE_ENABLED: bool = True
    JUDGE_EMBEDDED_WORKER: bool = True
    DOCKER_HOST: str | None = None

    # Rate limits (blueprint §7)
    RATE_LIMIT_LOGIN_PER_IP: int = 5
    RATE_LIMIT_LOGIN_WINDOW_SEC: int = 300
    RATE_LIMIT_SUBMIT_PER_USER: int = 10
    RATE_LIMIT_SUBMIT_WINDOW_SEC: int = 60
    RATE_LIMIT_API_PER_USER: int = 100
    RATE_LIMIT_API_WINDOW_SEC: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
