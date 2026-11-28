from typing import Any

from pydantic import ValidationError

from ridedesk.config.errors import ConfigError
from ridedesk.config.schema import BusinessConfig


def validate_config(data: Any, *, source: str) -> BusinessConfig:
    """Validate raw config data, raising ConfigError that names every bad field."""
    try:
        return BusinessConfig.model_validate(data)
    except ValidationError as error:
        raise ConfigError.from_validation(source, error) from error


__all__ = ["BusinessConfig", "ConfigError", "validate_config"]
