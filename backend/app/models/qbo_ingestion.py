"""
QBO ingestion models for versioned import runs and trial balance snapshots
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ClientGroupTaxYear(Base):
    """Client group tax-year context for scoped data access"""

    __tablename__ = "client_group_tax_years"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "client_group_id",
            "tax_year",
            name="uq_client_group_tax_year",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    client_group_id = Column(
        UUID(as_uuid=True),
        ForeignKey("client_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tax_year = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False, default="draft")
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    client_group = relationship("ClientGroup")


class ImportRun(Base):
    """Versioned QBO import run metadata"""

    __tablename__ = "import_runs"
    __table_args__ = (
        Index("idx_import_runs_entity_year", "entity_id", "tax_year"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True)
    client_group_id = Column(
        UUID(as_uuid=True),
        ForeignKey("client_groups.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    client_group_tax_year_id = Column(
        UUID(as_uuid=True),
        ForeignKey("client_group_tax_years.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    tax_year = Column(Integer, nullable=False)
    period_end_date = Column(Date, nullable=False)
    status = Column(String(30), nullable=False, default="queued")
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    triggered_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    error_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    entity = relationship("Entity")
    client_group = relationship("ClientGroup")
    client_group_tax_year = relationship("ClientGroupTaxYear")
    triggered_by = relationship("User")
    snapshots = relationship(
        "TrialBalanceSnapshot",
        back_populates="import_run",
        cascade="all, delete-orphan",
    )


class TrialBalanceAccount(Base):
    """Accounts referenced by trial balance lines"""

    __tablename__ = "trial_balance_accounts"
    __table_args__ = (
        Index("idx_trial_balance_accounts_entity", "entity_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True)
    external_account_id = Column(String(64), nullable=True)
    name = Column(String(255), nullable=False)
    account_type = Column(String(50), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    entity = relationship("Entity")


class TrialBalanceSnapshot(Base):
    """Immutable trial balance snapshots tied to import runs"""

    __tablename__ = "trial_balance_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "entity_id",
            "tax_year",
            "period_end_date",
            "snapshot_type",
            "run_type",
            "import_run_id",
            name="uq_trial_balance_snapshot",
        ),
        Index(
            "idx_trial_balance_snapshots_entity_year_period",
            "entity_id",
            "tax_year",
            "period_end_date",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True)
    import_run_id = Column(UUID(as_uuid=True), ForeignKey("import_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    tax_year = Column(Integer, nullable=False)
    period_end_date = Column(Date, nullable=False)
    snapshot_type = Column(String(30), nullable=False, default="MONTH_ACTIVITY")
    source = Column(String(30), nullable=False, default="QBO_IMPORTED")
    run_type = Column(String(30), nullable=False, default="IMPORT")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    import_run = relationship("ImportRun", back_populates="snapshots")
    lines = relationship("TrialBalanceLine", back_populates="snapshot", cascade="all, delete-orphan")
    entity = relationship("Entity")


class TrialBalanceLine(Base):
    """Line-level values for a trial balance snapshot"""

    __tablename__ = "trial_balance_lines"
    __table_args__ = (
        Index("idx_trial_balance_lines_snapshot", "snapshot_id"),
        Index("idx_trial_balance_lines_account", "account_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    snapshot_id = Column(
        UUID(as_uuid=True),
        ForeignKey("trial_balance_snapshots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("trial_balance_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount = Column(Numeric(18, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    snapshot = relationship("TrialBalanceSnapshot", back_populates="lines")
    account = relationship("TrialBalanceAccount")
    tenant = relationship("Tenant")
