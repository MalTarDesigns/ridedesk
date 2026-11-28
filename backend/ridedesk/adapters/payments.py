"""Online card payments. Manual methods (Zelle, cash, ...) need no provider:
their instructions come from the business config and are built in core code.
"""

import uuid
from decimal import Decimal
from typing import Protocol

from pydantic import BaseModel, Field, HttpUrl


class PaymentLink(BaseModel):
    url: HttpUrl
    provider_reference: str
    amount: Decimal
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    reference: str


class PaymentProvider(Protocol):
    def create_link(self, amount: Decimal, currency: str, reference: str) -> PaymentLink:
        """A link the customer pays through. Raises ValueError for a non-positive amount.

        The reference (the booking number) is kept with the payment, so a later
        webhook can be matched back to its booking.
        """
        ...


class MockPayments:
    def create_link(self, amount: Decimal, currency: str, reference: str) -> PaymentLink:
        if amount <= 0:
            raise ValueError("amount must be positive")
        provider_reference = f"mock-pay-{uuid.uuid4().hex}"
        return PaymentLink(
            url=HttpUrl(f"https://pay.example.test/{provider_reference}"),
            provider_reference=provider_reference,
            amount=amount,
            currency=currency,
            reference=reference,
        )
