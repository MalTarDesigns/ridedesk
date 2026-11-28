"""The shape of one business's configuration.

Defaults come from `verticals/<vertical>.yaml`, and each business's overrides
are merged over them. Every model forbids unknown keys, so a typo fails loudly
instead of being ignored.
"""

from datetime import time
from decimal import Decimal
from typing import Annotated, Literal, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    HttpUrl,
    StrictBool,
    StrictInt,
    ValidationError,
    model_validator,
)
from pydantic_core import InitErrorDetails, PydanticCustomError

Percent = Annotated[Decimal, Field(ge=0, le=100)]
Money = Annotated[Decimal, Field(ge=0, decimal_places=2)]
Key = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]*$", max_length=64)]
Weekday = Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def _quoted_clock_time(value: object) -> object:
    # YAML reads an unquoted 22:00 as the base-60 number 1320, which would
    # otherwise validate as 00:22. Only accept strings (or real times).
    if isinstance(value, str | time):
        return value
    raise ValueError('write times as quoted "HH:MM" strings')


def _naive(value: time) -> time:
    if value.tzinfo is not None:
        raise ValueError("times must not carry a timezone; the business timezone applies")
    return value


ClockTime = Annotated[time, BeforeValidator(_quoted_clock_time), AfterValidator(_naive)]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Contact(Strict):
    phone: str
    email: str


class OpeningHours(Strict):
    """One day's hours. A close at or before the open runs past midnight into the
    next day, so 18:00 to 02:00 is an overnight shift and 00:00 to 00:00 is 24 hours.
    """

    day: Weekday
    open: ClockTime
    close: ClockTime


class Branding(Strict):
    logo_url: HttpUrl | None = None
    primary_color: str = Field(default="#111111", pattern=r"^#[0-9a-fA-F]{6}$")
    accent_color: str = Field(default="#c9a227", pattern=r"^#[0-9a-fA-F]{6}$")
    font_family: str = "system-ui"


class Profile(Strict):
    # The timezone lives on the business record, the one source of truth for it.
    name: str
    contact: Contact
    hours: list[OpeningHours]
    service_area: str
    branding: Branding = Branding()


class VehicleClass(Strict):
    key: Key
    label: str
    passengers: StrictInt = Field(gt=0)
    luggage: StrictInt = Field(ge=0)


class TripType(Strict):
    key: Key
    label: str


class FormField(Strict):
    key: Key
    label: str
    type: Literal["text", "textarea", "address", "datetime", "number", "select", "email", "phone"]
    required: StrictBool = False
    options: list[str] = []


class HourlyPricing(Strict):
    rate: dict[str, Money]
    minimum_hours: StrictInt = Field(ge=1)


class AirportFlatRate(Strict):
    airport: str
    vehicle_class: Key
    amount: Money


class AfterHours(Strict):
    start: ClockTime
    end: ClockTime
    surcharge_percent: Percent


class Pricing(Strict):
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    base_fare: dict[str, Money]
    per_mile: Money
    hourly: HourlyPricing
    airport_flat_rates: list[AirportFlatRate] = []
    after_hours: AfterHours | None = None
    gratuity_percent: Percent = Decimal(0)


class Flags(Strict):
    large_group_passengers: StrictInt = Field(gt=0)
    last_minute_hours: StrictInt = Field(ge=0)
    long_distance_miles: StrictInt = Field(gt=0)


class PaymentMethod(Strict):
    key: Key
    kind: Literal["manual", "automatic"]
    display_name: str
    instructions: str
    handle: str | None = None
    qr_image_url: HttpUrl | None = None
    deposit_percent: Percent = Decimal(0)
    instant: StrictBool = False
    enabled: StrictBool = False


class MessageTemplate(Strict):
    subject: str
    body: str


class Agent(Strict):
    tone: str
    instructions: str
    suggestable_flags: list[Key] = []
    actions_needing_approval: list[Key] = []


class Reminders(Strict):
    hours_before: StrictInt = Field(gt=0)
    auto_send: StrictBool = False


class Reports(Strict):
    metrics: list[Key]


class BusinessConfig(Strict):
    placeholder: StrictBool = False
    profile: Profile
    vehicle_classes: list[VehicleClass] = Field(min_length=1)
    trip_types: list[TripType] = Field(min_length=1)
    form_fields: list[FormField] = Field(min_length=1)
    pricing: Pricing
    flags: Flags
    payment_methods: list[PaymentMethod]
    templates: dict[Key, MessageTemplate]
    agent: Agent
    reminders: Reminders
    reports: Reports

    @model_validator(mode="after")
    def _check_references(self) -> Self:
        # Rules that span sections, raised with their own field paths so a form
        # can point at the exact field. They run however the model is built.
        if problems := reference_problems(self):
            raise ValidationError.from_exception_data(
                "BusinessConfig",
                [
                    InitErrorDetails(
                        type=PydanticCustomError("config_reference", message),
                        loc=path,
                        input=None,
                    )
                    for path, message in problems
                ],
            )
        return self


FieldPath = tuple[str | int, ...]


def reference_problems(config: BusinessConfig) -> list[tuple[FieldPath, str]]:
    """Rules that span sections, each reported at the path a form can point to."""
    problems: list[tuple[FieldPath, str]] = []

    for section, keys in {
        "vehicle_classes": [v.key for v in config.vehicle_classes],
        "trip_types": [t.key for t in config.trip_types],
        "form_fields": [f.key for f in config.form_fields],
        "payment_methods": [p.key for p in config.payment_methods],
    }.items():
        for index, key in enumerate(keys):
            if key in keys[:index]:
                problems.append(((section, index, "key"), f"duplicate key {key!r}"))

    known = {v.key for v in config.vehicle_classes}
    for path, prices in {
        ("pricing", "base_fare"): config.pricing.base_fare,
        ("pricing", "hourly", "rate"): config.pricing.hourly.rate,
    }.items():
        for key in sorted(set(prices) - known):
            problems.append(((*path, key), f"unknown vehicle class {key!r}"))
        for key in sorted(known - set(prices)):
            problems.append((path, f"missing a price for vehicle class {key!r}"))
    for index, rate in enumerate(config.pricing.airport_flat_rates):
        if rate.vehicle_class not in known:
            problems.append(
                (
                    ("pricing", "airport_flat_rates", index, "vehicle_class"),
                    f"unknown vehicle class {rate.vehicle_class!r}",
                )
            )

    for index, form_field in enumerate(config.form_fields):
        if form_field.type == "select" and not form_field.options:
            problems.append((("form_fields", index, "options"), "a select field needs options"))

    days = [h.day for h in config.profile.hours]
    for index, hours in enumerate(config.profile.hours):
        if hours.day in days[:index]:
            problems.append((("profile", "hours", index, "day"), f"duplicate day {hours.day!r}"))

    return problems
