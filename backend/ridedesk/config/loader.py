"""Load a business's config: vertical defaults with its overrides merged on top."""

import copy
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic_core import to_jsonable_python
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from ridedesk.config import validate_config
from ridedesk.config.errors import ConfigError
from ridedesk.config.schema import BusinessConfig
from ridedesk.models import Business, BusinessConfigOverride


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Merge override into a copy of base. Mappings merge by key; lists replace whole."""
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


VERTICAL_NAME = re.compile(r"^[a-z][a-z0-9_]*$")


def read_vertical(name: str, verticals_dir: Path) -> dict[str, Any]:
    if not VERTICAL_NAME.match(name):
        raise ConfigError(name, ["a vertical name is lowercase letters, digits and underscores"])
    path = verticals_dir / f"{name}.yaml"
    try:
        data = yaml.safe_load(path.read_text())
    except FileNotFoundError as error:
        raise ConfigError(path.name, ["no such vertical file"]) from error
    except yaml.YAMLError as error:
        raise ConfigError(path.name, [f"not valid YAML ({error})"]) from error
    if not isinstance(data, dict):
        raise ConfigError(path.name, ["the file must hold a mapping at the top level"])
    return data


def load_vertical(name: str, verticals_dir: Path) -> BusinessConfig:
    return validate_config(read_vertical(name, verticals_dir), source=f"{name}.yaml")


def _stored_overrides(session: Session, business: Business) -> BusinessConfigOverride | None:
    return session.scalars(
        select(BusinessConfigOverride).where(BusinessConfigOverride.business_id == business.id)
    ).one_or_none()


def resolve_config(session: Session, business: Business, verticals_dir: Path) -> BusinessConfig:
    defaults = read_vertical(business.vertical, verticals_dir)
    stored = _stored_overrides(session, business)
    merged = deep_merge(defaults, stored.data) if stored else defaults
    return validate_config(merged, source=f"{business.slug} config")


def save_overrides(
    session: Session, business: Business, overrides: dict[str, Any], verticals_dir: Path
) -> BusinessConfig:
    """Replace a business's overrides, after checking the merged result is valid.

    The whole override document is replaced, so callers send every key the
    owner has changed, not only the latest edit. Values are stored in their
    JSON form (Decimals and times as strings), and nothing is written when the
    merged config fails validation.
    """
    data = to_jsonable_python(overrides)
    defaults = read_vertical(business.vertical, verticals_dir)
    config = validate_config(deep_merge(defaults, data), source=f"{business.slug} config")

    # One row per business; an upsert keeps two first saves from colliding.
    statement = insert(BusinessConfigOverride).values(business_id=business.id, data=data)
    session.execute(
        statement.on_conflict_do_update(
            index_elements=[BusinessConfigOverride.business_id],
            set_={"data": statement.excluded.data, "updated_at": func.now()},
        )
    )
    return config
