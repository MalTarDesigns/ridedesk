from decimal import Decimal

import pytest

from ridedesk.adapters.maps import MapsProvider


def test_a_route_has_positive_distance_and_time(maps: MapsProvider) -> None:
    route = maps.distance("JFK Airport, Queens, NY", "Times Square, New York, NY")

    assert route.miles > Decimal(0)
    assert route.minutes > 0


def test_the_same_trip_gives_the_same_route(maps: MapsProvider) -> None:
    first = maps.distance("JFK Airport", "Times Square")
    second = maps.distance("JFK Airport", "Times Square")

    assert first == second


@pytest.mark.parametrize(("origin", "destination"), [("", "Times Square"), ("JFK", "  ")])
def test_a_blank_address_is_rejected(maps: MapsProvider, origin: str, destination: str) -> None:
    with pytest.raises(ValueError):
        maps.distance(origin, destination)
