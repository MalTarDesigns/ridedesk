"""Every registered implementation of an interface runs the same contract suite.

A real provider joins by adding itself to its table in the registry. One whose
settings are missing raises ProviderNotConfiguredError and is skipped, so live
providers only run when their keys are set.
"""

from collections.abc import Callable
from typing import Any

import pytest

from ridedesk.adapters import registry
from ridedesk.settings import Settings


def implementations(table: dict[str, Callable[[Settings], Any]]) -> Any:
    names = sorted(table)

    @pytest.fixture(params=names, ids=names)
    def build(request: pytest.FixtureRequest) -> Any:
        try:
            return table[request.param](Settings())
        except registry.ProviderNotConfiguredError as missing:
            pytest.skip(f"{request.param} is not configured: {missing}")

    return build


maps = implementations(registry.MAPS)
calendar = implementations(registry.CALENDAR)
email = implementations(registry.EMAIL)
sms = implementations(registry.SMS)
payments = implementations(registry.PAYMENTS)
llm = implementations(registry.LLM)
