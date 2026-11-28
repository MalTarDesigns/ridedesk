import hashlib
from decimal import Decimal
from typing import Protocol

from pydantic import BaseModel


class Route(BaseModel):
    miles: Decimal
    minutes: int


class MapsProvider(Protocol):
    def distance(self, origin: str, destination: str) -> Route:
        """Driving distance and time. Raises ValueError for a blank address."""
        ...


class MockMaps:
    """Stable, made-up distances: the same two addresses always give the same route."""

    def distance(self, origin: str, destination: str) -> Route:
        if not origin.strip() or not destination.strip():
            raise ValueError("origin and destination are required")
        key = f"{origin.strip().lower()}|{destination.strip().lower()}".encode()
        miles = 1 + int(hashlib.sha256(key).hexdigest()[:4], 16) % 60
        return Route(miles=Decimal(miles), minutes=miles * 2)
