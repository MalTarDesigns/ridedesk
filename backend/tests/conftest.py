import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

import ridedesk.models  # noqa: F401  (registers every model on Base.metadata)
from ridedesk.main import create_app
from ridedesk.settings import Settings

BACKEND_DIR = Path(__file__).resolve().parent.parent


class SuiteSettings(BaseSettings):
    """Read like the app's settings: environment first, then backend/.env."""

    model_config = SettingsConfigDict(
        env_prefix="RIDEDESK_", env_file=BACKEND_DIR / ".env", extra="ignore"
    )

    # An admin connection to a Postgres server. Each test session creates its
    # own database on it, migrates it, and drops it at the end.
    test_database_url: str = "postgresql+psycopg://ridedesk:ridedesk@localhost:5432/postgres"


ADMIN_URL = SuiteSettings().test_database_url


def alembic_config(database_url: str) -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    # ConfigParser treats % as interpolation, so escape it (URL-encoded passwords).
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return config


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    name = f"ridedesk_test_{uuid.uuid4().hex[:12]}"
    admin = create_engine(ADMIN_URL, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{name}"'))
    url = make_url(ADMIN_URL).set(database=name).render_as_string(hide_password=False)
    try:
        command.upgrade(alembic_config(url), "head")
        yield url
    finally:
        with admin.connect() as conn:
            conn.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        admin.dispose()


@pytest.fixture
def client(database_url: str) -> Iterator[TestClient]:
    with TestClient(create_app(Settings(database_url=database_url))) as test_client:
        yield test_client
