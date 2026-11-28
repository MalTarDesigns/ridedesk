import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from ridedesk.db import Base, TimestampMixin


class Business(TimestampMixin, Base):
    """The tenant. Every other record belongs to exactly one business."""

    __tablename__ = "businesses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    timezone: Mapped[str] = mapped_column(String(64))
