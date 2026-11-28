"""add business vertical and config overrides

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add the column nullable, backfill, then require it, so the migration also
    # runs on a database that already holds businesses. Every business created
    # before verticals existed was a car service, the only vertical at the time.
    op.add_column("businesses", sa.Column("vertical", sa.String(length=64), nullable=True))
    op.execute("UPDATE businesses SET vertical = 'car_service' WHERE vertical IS NULL")
    op.alter_column("businesses", "vertical", nullable=False)

    op.create_table(
        "business_config_overrides",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("business_id", sa.Uuid(), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["business_id"],
            ["businesses.id"],
            name=op.f("fk_business_config_overrides_business_id_businesses"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_business_config_overrides")),
        sa.UniqueConstraint("business_id", name=op.f("uq_business_config_overrides_business_id")),
    )


def downgrade() -> None:
    op.drop_table("business_config_overrides")
    op.drop_column("businesses", "vertical")
