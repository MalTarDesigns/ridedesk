import uuid
from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
import yaml
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from ridedesk.config import ConfigError
from ridedesk.config.loader import deep_merge, load_vertical, resolve_config, save_overrides
from ridedesk.models import Business, BusinessConfigOverride
from tests.factories import minimal_config


@pytest.fixture
def verticals_dir(tmp_path: Path) -> Path:
    (tmp_path / "test_vertical.yaml").write_text(yaml.safe_dump(minimal_config()))
    return tmp_path


@pytest.fixture
def session(database_url: str) -> Iterator[Session]:
    engine = create_engine(database_url)
    with Session(engine) as db:
        yield db
        db.rollback()
    engine.dispose()


@pytest.fixture
def business(session: Session) -> Business:
    business = Business(
        slug=f"test-{uuid.uuid4().hex[:8]}",
        name="Test Rides",
        timezone="America/New_York",
        vertical="test_vertical",
    )
    session.add(business)
    session.flush()
    return business


def test_deep_merge_merges_mappings_and_replaces_lists() -> None:
    base: dict[str, Any] = {"pricing": {"per_mile": "3", "currency": "USD"}, "trip_types": [1, 2]}
    override = {"pricing": {"per_mile": "4"}, "trip_types": [3]}

    assert deep_merge(base, override) == {
        "pricing": {"per_mile": "4", "currency": "USD"},
        "trip_types": [3],
    }
    assert base["pricing"]["per_mile"] == "3"  # inputs are not mutated


def test_an_invalid_vertical_file_names_the_file_and_field(verticals_dir: Path) -> None:
    data = minimal_config()
    data["flags"]["long_distance_miles"] = -5
    (verticals_dir / "broken.yaml").write_text(yaml.safe_dump(data))

    with pytest.raises(ConfigError) as caught:
        load_vertical("broken", verticals_dir)

    assert str(caught.value).startswith("broken.yaml:")
    assert "flags.long_distance_miles" in str(caught.value)


def test_a_business_without_overrides_gets_the_vertical_defaults(
    session: Session, business: Business, verticals_dir: Path
) -> None:
    config = resolve_config(session, business, verticals_dir)

    assert config.pricing.per_mile == Decimal("3.00")


def test_stored_overrides_merge_over_the_defaults(
    session: Session, business: Business, verticals_dir: Path
) -> None:
    save_overrides(session, business, {"pricing": {"per_mile": "4.25"}}, verticals_dir)

    config = resolve_config(session, business, verticals_dir)

    assert config.pricing.per_mile == Decimal("4.25")
    assert config.pricing.currency == "USD"  # untouched defaults survive


def test_an_invalid_override_is_rejected_and_nothing_is_stored(
    session: Session, business: Business, verticals_dir: Path
) -> None:
    with pytest.raises(ConfigError) as caught:
        save_overrides(session, business, {"pricing": {"per_mile": "free"}}, verticals_dir)

    assert "pricing.per_mile" in str(caught.value)
    stored = session.scalars(
        select(BusinessConfigOverride).where(BusinessConfigOverride.business_id == business.id)
    ).all()
    assert stored == []


def test_saving_again_replaces_the_previous_overrides(
    session: Session, business: Business, verticals_dir: Path
) -> None:
    save_overrides(session, business, {"pricing": {"per_mile": "4.25"}}, verticals_dir)
    save_overrides(session, business, {"pricing": {"gratuity_percent": "18"}}, verticals_dir)

    config = resolve_config(session, business, verticals_dir)

    assert config.pricing.per_mile == Decimal("3.00")
    assert config.pricing.gratuity_percent == Decimal("18")


def test_overrides_are_stored_in_json_form(
    session: Session, business: Business, verticals_dir: Path
) -> None:
    save_overrides(session, business, {"pricing": {"per_mile": Decimal("4.10")}}, verticals_dir)

    stored = session.scalars(
        select(BusinessConfigOverride.data).where(BusinessConfigOverride.business_id == business.id)
    ).one()
    assert stored == {"pricing": {"per_mile": "4.10"}}
    assert resolve_config(session, business, verticals_dir).pricing.per_mile == Decimal("4.10")


def test_a_vertical_name_cannot_reach_outside_the_folder(verticals_dir: Path) -> None:
    with pytest.raises(ConfigError):
        load_vertical("../secrets", verticals_dir)
