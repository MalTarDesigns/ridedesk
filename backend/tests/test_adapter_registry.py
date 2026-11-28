from collections.abc import Mapping
from typing import get_args

import pytest
from pydantic import ValidationError

from ridedesk.adapters import registry
from ridedesk.adapters.maps import MockMaps
from ridedesk.settings import Settings

TABLES: dict[str, Mapping[str, object]] = {
    "maps": registry.MAPS,
    "calendar": registry.CALENDAR,
    "email": registry.EMAIL,
    "sms": registry.SMS,
    "payments": registry.PAYMENTS,
    "llm": registry.LLM,
}


@pytest.mark.parametrize("interface", sorted(TABLES))
def test_each_setting_offers_exactly_the_registered_providers(interface: str) -> None:
    annotation = Settings.model_fields[f"{interface}_provider"].annotation

    assert set(get_args(annotation)) == set(TABLES[interface])
    assert "mock" in TABLES[interface]


def test_the_provider_is_chosen_by_environment_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RIDEDESK_MAPS_PROVIDER", "mock")

    adapters = registry.build_adapters(Settings())

    assert isinstance(adapters.maps, MockMaps)


def test_an_unknown_provider_fails_at_startup_naming_the_setting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RIDEDESK_MAPS_PROVIDER", "google")

    with pytest.raises(ValidationError) as caught:
        Settings()

    assert "maps_provider" in str(caught.value)
    assert "'mock'" in str(caught.value)
