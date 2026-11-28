from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect

from ridedesk.db import Base


def test_migrations_create_businesses(database_url: str) -> None:
    engine = create_engine(database_url)
    try:
        columns = {c["name"] for c in inspect(engine).get_columns("businesses")}
    finally:
        engine.dispose()

    assert columns == {"id", "slug", "name", "timezone", "vertical", "created_at", "updated_at"}


def test_models_match_migrations(database_url: str) -> None:
    # Fails when a model changes without a matching Alembic revision.
    engine = create_engine(database_url)
    try:
        with engine.connect() as conn:
            diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    finally:
        engine.dispose()

    assert diff == []
