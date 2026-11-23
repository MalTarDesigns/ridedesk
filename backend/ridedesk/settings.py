from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings, read from RIDEDESK_* environment variables."""

    model_config = SettingsConfigDict(env_prefix="RIDEDESK_", env_file=".env", extra="ignore")

    # The default matches the local Docker Compose database. Every other
    # environment sets RIDEDESK_DATABASE_URL.
    database_url: str = "postgresql+psycopg://ridedesk:ridedesk@localhost:5432/ridedesk"


@lru_cache
def get_settings() -> Settings:
    return Settings()
