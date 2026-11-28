from decimal import Decimal

import pytest

from ridedesk.adapters.payments import PaymentProvider


def test_a_link_keeps_the_amount_currency_and_booking_reference(
    payments: PaymentProvider,
) -> None:
    link = payments.create_link(Decimal("120.00"), "USD", "RD-1042")

    assert link.amount == Decimal("120.00")
    assert link.currency == "USD"
    assert link.reference == "RD-1042"
    assert link.provider_reference
    assert link.url.scheme == "https"


def test_each_link_gets_its_own_provider_reference(payments: PaymentProvider) -> None:
    first = payments.create_link(Decimal("120.00"), "USD", "RD-1042")
    second = payments.create_link(Decimal("120.00"), "USD", "RD-1042")

    assert first.provider_reference != second.provider_reference


@pytest.mark.parametrize("amount", [Decimal(0), Decimal("-5")])
def test_a_non_positive_amount_is_rejected(payments: PaymentProvider, amount: Decimal) -> None:
    with pytest.raises(ValueError):
        payments.create_link(amount, "USD", "RD-1042")
