from decimal import Decimal
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from ridedesk.config import BusinessConfig, ConfigError, validate_config
from tests.factories import minimal_config


def test_a_valid_config_parses_money_as_decimal() -> None:
    config = validate_config(minimal_config(), source="test")

    assert isinstance(config, BusinessConfig)
    assert config.pricing.per_mile == Decimal("3.00")


def test_an_unknown_key_is_rejected_by_its_path() -> None:
    data = minimal_config()
    data["pricing"]["per_miles"] = "3.00"  # typo

    with pytest.raises(ConfigError) as caught:
        validate_config(data, source="test")

    assert "pricing.per_miles" in str(caught.value)


def test_a_bad_type_names_the_field_and_the_source() -> None:
    data = minimal_config()
    data["pricing"]["per_mile"] = "three dollars"

    with pytest.raises(ConfigError) as caught:
        validate_config(data, source="car_service.yaml")

    message = str(caught.value)
    assert message.startswith("car_service.yaml:")
    assert "pricing.per_mile" in message


def test_base_fare_must_name_known_vehicle_classes() -> None:
    data = minimal_config()
    data["pricing"]["base_fare"]["limo"] = "90.00"

    with pytest.raises(ConfigError) as caught:
        validate_config(data, source="test")

    assert caught.value.problems == ["pricing.base_fare.limo: unknown vehicle class 'limo'"]


def test_every_vehicle_class_needs_a_base_fare_and_an_hourly_rate() -> None:
    data = minimal_config()
    data["vehicle_classes"].append({"key": "suv", "label": "SUV", "passengers": 6, "luggage": 6})

    with pytest.raises(ConfigError) as caught:
        validate_config(data, source="test")

    assert caught.value.problems == [
        "pricing.base_fare: missing a price for vehicle class 'suv'",
        "pricing.hourly.rate: missing a price for vehicle class 'suv'",
    ]


def test_an_unquoted_yaml_time_is_rejected_not_misread() -> None:
    data = minimal_config()
    data["profile"]["hours"][0]["close"] = yaml.safe_load("close: 22:00")["close"]  # 1320

    with pytest.raises(ConfigError) as caught:
        validate_config(data, source="test")

    assert "profile.hours.0.close" in str(caught.value)


def test_a_time_with_a_timezone_is_rejected() -> None:
    data = minimal_config()
    data["pricing"]["after_hours"]["start"] = "22:00+05:00"

    with pytest.raises(ConfigError) as caught:
        validate_config(data, source="test")

    assert "pricing.after_hours.start" in str(caught.value)


def test_overnight_and_24_hour_days_are_allowed() -> None:
    data = minimal_config()
    data["profile"]["hours"] = [
        {"day": "fri", "open": "18:00", "close": "02:00"},
        {"day": "sat", "open": "00:00", "close": "00:00"},
    ]

    config = validate_config(data, source="test")

    assert [h.day for h in config.profile.hours] == ["fri", "sat"]


def test_each_day_appears_once() -> None:
    data = minimal_config()
    data["profile"]["hours"].append({"day": "mon", "open": "08:00", "close": "12:00"})

    with pytest.raises(ConfigError) as caught:
        validate_config(data, source="test")

    assert caught.value.problems == ["profile.hours.1.day: duplicate day 'mon'"]


def test_the_rules_hold_even_when_the_model_is_built_directly() -> None:
    data = minimal_config()
    data["pricing"]["base_fare"]["limo"] = "90.00"

    with pytest.raises(ValidationError) as caught:
        BusinessConfig.model_validate(data)

    assert caught.value.errors()[0]["loc"] == ("pricing", "base_fare", "limo")


def test_a_select_field_needs_options() -> None:
    data = minimal_config()
    data["form_fields"].append({"key": "vehicle", "label": "Vehicle", "type": "select"})

    with pytest.raises(ConfigError) as caught:
        validate_config(data, source="test")

    assert caught.value.problems == ["form_fields.2.options: a select field needs options"]


def test_numbers_and_switches_are_not_coerced_from_other_types() -> None:
    data = minimal_config()
    data["flags"]["large_group_passengers"] = True
    data["reminders"]["auto_send"] = "yes"

    with pytest.raises(ConfigError) as caught:
        validate_config(data, source="test")

    assert "flags.large_group_passengers" in str(caught.value)
    assert "reminders.auto_send" in str(caught.value)


def test_form_field_keys_must_be_unique() -> None:
    data = minimal_config()
    data["form_fields"].append(dict(data["form_fields"][0]))

    with pytest.raises(ConfigError) as caught:
        validate_config(data, source="test")

    assert caught.value.problems == ["form_fields.2.key: duplicate key 'pickup'"]


def test_percentages_must_be_between_0_and_100() -> None:
    data = minimal_config()
    data["pricing"]["gratuity_percent"] = "120"

    with pytest.raises(ConfigError) as caught:
        validate_config(data, source="test")

    assert "pricing.gratuity_percent" in str(caught.value)


def test_the_car_service_defaults_are_valid_and_marked_placeholder() -> None:
    path = Path(__file__).resolve().parent.parent / "verticals" / "car_service.yaml"
    config = validate_config(yaml.safe_load(path.read_text()), source=path.name)

    assert config.placeholder is True
    assert {v.key for v in config.vehicle_classes} == {"sedan", "suv", "sprinter"}
