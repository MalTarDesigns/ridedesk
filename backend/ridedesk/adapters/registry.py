"""Pick each external service's implementation from settings.

Each table is typed by its interface, so mypy rejects a provider whose methods
do not match. A real provider is one more entry, and the contract tests in
tests/contracts/ then run against it too.
"""

from collections.abc import Callable
from dataclasses import dataclass

from ridedesk.adapters.calendar import CalendarProvider, MockCalendar
from ridedesk.adapters.llm import LlmClient, MockLlm
from ridedesk.adapters.maps import MapsProvider, MockMaps
from ridedesk.adapters.messages import EmailSender, MockEmail, MockSms, SmsSender
from ridedesk.adapters.payments import MockPayments, PaymentProvider
from ridedesk.settings import Settings


class ProviderNotConfiguredError(RuntimeError):
    """A real provider whose settings (an API key, say) are missing.

    Contract tests skip a provider that raises this, so live providers only run
    when their keys are set.
    """


MAPS: dict[str, Callable[[Settings], MapsProvider]] = {"mock": lambda _: MockMaps()}
CALENDAR: dict[str, Callable[[Settings], CalendarProvider]] = {"mock": lambda _: MockCalendar()}
EMAIL: dict[str, Callable[[Settings], EmailSender]] = {"mock": lambda _: MockEmail()}
SMS: dict[str, Callable[[Settings], SmsSender]] = {"mock": lambda _: MockSms()}
PAYMENTS: dict[str, Callable[[Settings], PaymentProvider]] = {"mock": lambda _: MockPayments()}
LLM: dict[str, Callable[[Settings], LlmClient]] = {"mock": lambda _: MockLlm()}


@dataclass(frozen=True)
class Adapters:
    maps: MapsProvider
    calendar: CalendarProvider
    email: EmailSender
    sms: SmsSender
    payments: PaymentProvider
    llm: LlmClient


def build_adapters(settings: Settings) -> Adapters:
    return Adapters(
        maps=MAPS[settings.maps_provider](settings),
        calendar=CALENDAR[settings.calendar_provider](settings),
        email=EMAIL[settings.email_provider](settings),
        sms=SMS[settings.sms_provider](settings),
        payments=PAYMENTS[settings.payments_provider](settings),
        llm=LLM[settings.llm_provider](settings),
    )
