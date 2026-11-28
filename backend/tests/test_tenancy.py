import uuid

from sqlalchemy import Column, ForeignKey, MetaData, Table, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from ridedesk.db import Base, TenantMixin

TENANT_ROOT = "businesses"


def tables_missing_tenant_key(metadata: MetaData) -> list[str]:
    """Names of tables, other than the tenant root, without a business_id FK to it."""
    missing = []
    for table in metadata.sorted_tables:
        if table.name == TENANT_ROOT:
            continue
        column = table.columns.get("business_id")
        points_at_root = column is not None and any(
            fk.column.table.name == TENANT_ROOT for fk in column.foreign_keys
        )
        if not points_at_root:
            missing.append(table.name)
    return missing


def test_rule_flags_a_table_without_business_id() -> None:
    metadata = MetaData()
    Table(TENANT_ROOT, metadata, Column("id", Uuid, primary_key=True))
    Table(
        "good",
        metadata,
        Column("id", Uuid, primary_key=True),
        Column("business_id", Uuid, ForeignKey(f"{TENANT_ROOT}.id")),
    )
    Table("bad", metadata, Column("id", Uuid, primary_key=True))

    assert tables_missing_tenant_key(metadata) == ["bad"]


def test_every_model_table_carries_business_id() -> None:
    # Guard against an empty registry, which would make the rule pass vacuously.
    assert TENANT_ROOT in Base.metadata.tables
    assert tables_missing_tenant_key(Base.metadata) == []


def test_tenant_mixin_adds_a_required_indexed_foreign_key() -> None:
    class ScratchBase(DeclarativeBase):
        pass

    class Root(ScratchBase):
        __tablename__ = TENANT_ROOT
        id: Mapped[uuid.UUID] = mapped_column(primary_key=True)

    class Ride(TenantMixin, ScratchBase):
        __tablename__ = "rides"
        id: Mapped[uuid.UUID] = mapped_column(primary_key=True)

    column = Ride.__table__.columns["business_id"]
    assert column.nullable is False
    assert column.index is True
    assert tables_missing_tenant_key(ScratchBase.metadata) == []
