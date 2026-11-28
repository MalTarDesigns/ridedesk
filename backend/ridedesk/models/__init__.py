"""Importing this package registers every model on Base.metadata."""

from ridedesk.models.business import Business
from ridedesk.models.config_override import BusinessConfigOverride

__all__ = ["Business", "BusinessConfigOverride"]
