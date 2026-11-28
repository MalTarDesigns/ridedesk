import uuid
from typing import Any

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ridedesk.db import Base, TenantMixin, TimestampMixin


class BusinessConfigOverride(TenantMixin, TimestampMixin, Base):
    """One business's changes to its vertical's default config.

    Holds only the keys the owner changed. The full config is the vertical
    defaults with this merged on top, validated as a whole.
    """

    __tablename__ = "business_config_overrides"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # One row per business: the unique index replaces the mixin's plain one.
    business_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), unique=True
    )
    data: Mapped[dict[str, Any]] = mapped_column(JSONB)
