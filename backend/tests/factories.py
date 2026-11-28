"""A small, valid config dict that tests copy and break on purpose."""

import copy
from typing import Any

_MINIMAL: dict[str, Any] = {
    "placeholder": True,
    "profile": {
        "name": "Test Rides",
        "contact": {"phone": "+1 555 0100", "email": "owner@example.com"},
        "hours": [{"day": "mon", "open": "08:00", "close": "22:00"}],
        "service_area": "Test County",
    },
    "vehicle_classes": [{"key": "sedan", "label": "Sedan", "passengers": 3, "luggage": 3}],
    "trip_types": [{"key": "point_to_point", "label": "Point to point"}],
    "form_fields": [
        {"key": "pickup", "label": "Pickup", "type": "address", "required": True},
        {"key": "notes", "label": "Notes", "type": "textarea", "required": False},
    ],
    "pricing": {
        "currency": "USD",
        "base_fare": {"sedan": "50.00"},
        "per_mile": "3.00",
        "hourly": {"rate": {"sedan": "75.00"}, "minimum_hours": 2},
        "airport_flat_rates": [],
        "after_hours": {"start": "22:00", "end": "06:00", "surcharge_percent": "15"},
        "gratuity_percent": "20",
    },
    "flags": {
        "large_group_passengers": 6,
        "last_minute_hours": 12,
        "long_distance_miles": 100,
    },
    "payment_methods": [
        {
            "key": "cash",
            "kind": "manual",
            "display_name": "Cash",
            "instructions": "Pay the driver.",
            "enabled": True,
        }
    ],
    "templates": {"confirmation": {"subject": "Booked", "body": "See you soon."}},
    "agent": {
        "tone": "warm and professional",
        "instructions": "Parse booking requests.",
        "suggestable_flags": ["special_request"],
        "actions_needing_approval": ["send_reply"],
    },
    "reminders": {"hours_before": 24, "auto_send": False},
    "reports": {"metrics": ["bookings", "revenue"]},
}


def minimal_config() -> dict[str, Any]:
    return copy.deepcopy(_MINIMAL)
