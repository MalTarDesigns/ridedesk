from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings, read from RIDEDESK_* environment variables."""

    model_config = SettingsConfigDict(env_prefix="RIDEDESK_", env_file=".env", extra="ignore")

    # The default matches the local Docker Compose database. Every other
    # environment sets RIDEDESK_DATABASE_URL.
    database_url: str = "postgresql+psycopg://ridedesk:ridedesk@localhost:5432/ridedesk"

    # Folder holding verticals/<vertical>.yaml default configs.
    verticals_dir: Path = Path(__file__).resolve().parent.parent / "verticals"

    # Which implementation backs each external service. "mock" needs no keys.
    maps_provider: Literal["mock"] = "mock"
    calendar_provider: Literal["mock"] = "mock"
    email_provider: Literal["mock"] = "mock"
    sms_provider: Literal["mock"] = "mock"
    payments_provider: Literal["mock"] = "mock"
    llm_provider: Literal["mock"] = "mock"


@lru_cache
def get_settings() -> Settings:
    return Settings()
