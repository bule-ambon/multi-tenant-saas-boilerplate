"""Add QBO ingestion persistence and metadata

Revision ID: 005
Revises: 004
Create Date: 2024-02-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

# revision identifiers, used by Alembic.
revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add metadata columns, tax-year context, and trial balance tables"""
    op.add_column(
        "entities",
        sa.Column(
            "entity_type",
            sa.String(50),
            nullable=False,
            server_default="Individual",
        ),
    )
    op.add_column(
        "entities",
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default="active",
        ),
    )
    op.add_column("client_group_entities", sa.Column("start_date", sa.Date(), nullable=True))
    op.add_column("client_group_entities", sa.Column("end_date", sa.Date(), nullable=True))
    op.add_column("client_group_entities", sa.Column("tags", sa.Text, nullable=True))
    op.add_column("client_group_entities", sa.Column("notes", sa.Text, nullable=True))

    op.create_table(
        "client_group_tax_years",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "tenant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "client_group_id",
            UUID(as_uuid=True),
            sa.ForeignKey("client_groups.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tax_year", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_client_group_tax_years_tenant", "client_group_tax_years", ["tenant_id"])
    op.create_index("idx_client_group_tax_years_group", "client_group_tax_years", ["client_group_id"])
    op.create_unique_constraint(
        "uq_client_group_tax_year",
        "client_group_tax_years",
        ["tenant_id", "client_group_id", "tax_year"],
    )

    op.create_table(
        "import_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "tenant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "entity_id",
            UUID(as_uuid=True),
            sa.ForeignKey("entities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "client_group_id",
            UUID(as_uuid=True),
            sa.ForeignKey("client_groups.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "client_group_tax_year_id",
            UUID(as_uuid=True),
            sa.ForeignKey("client_group_tax_years.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("tax_year", sa.Integer(), nullable=False),
        sa.Column("period_end_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="queued"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "triggered_by_user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("error_text", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_import_runs_tenant", "import_runs", ["tenant_id"])
    op.create_index("idx_import_runs_entity_year", "import_runs", ["entity_id", "tax_year"])
    op.create_index("idx_import_runs_group", "import_runs", ["client_group_id"])

    op.create_table(
        "trial_balance_accounts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "tenant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "entity_id",
            UUID(as_uuid=True),
            sa.ForeignKey("entities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("external_account_id", sa.String(64), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("account_type", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_trial_balance_accounts_entity", "trial_balance_accounts", ["entity_id"])

    op.create_table(
        "trial_balance_snapshots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "tenant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "entity_id",
            UUID(as_uuid=True),
            sa.ForeignKey("entities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "import_run_id",
            UUID(as_uuid=True),
            sa.ForeignKey("import_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tax_year", sa.Integer(), nullable=False),
        sa.Column("period_end_date", sa.Date(), nullable=False),
        sa.Column("snapshot_type", sa.String(30), nullable=False, server_default="MONTH_ACTIVITY"),
        sa.Column("source", sa.String(30), nullable=False, server_default="QBO_IMPORTED"),
        sa.Column("run_type", sa.String(30), nullable=False, server_default="IMPORT"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_trial_balance_snapshots_entity_period", "trial_balance_snapshots", ["entity_id", "tax_year", "period_end_date"])
    op.create_unique_constraint(
        "uq_trial_balance_snapshot",
        "trial_balance_snapshots",
        ["entity_id", "tax_year", "period_end_date", "snapshot_type", "run_type", "import_run_id"],
    )

    op.create_table(
        "trial_balance_lines",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "tenant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "snapshot_id",
            UUID(as_uuid=True),
            sa.ForeignKey("trial_balance_snapshots.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "account_id",
            UUID(as_uuid=True),
            sa.ForeignKey("trial_balance_accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_trial_balance_lines_snapshot", "trial_balance_lines", ["snapshot_id"])
    op.create_index("idx_trial_balance_lines_account", "trial_balance_lines", ["account_id"])

    for table in (
        "client_group_tax_years",
        "import_runs",
        "trial_balance_accounts",
        "trial_balance_snapshots",
        "trial_balance_lines",
    ):
        op.execute(f'ALTER TABLE {table} ENABLE ROW LEVEL SECURITY')
        op.execute(
            f"""
        CREATE POLICY tenant_isolation_policy_{table} ON {table}
        FOR ALL
        USING (tenant_id::text = current_setting('app.current_tenant_id', true))
    """
        )


def downgrade() -> None:
    """Drop trial balance tables and metadata columns"""
    for table in (
        "trial_balance_lines",
        "trial_balance_snapshots",
        "trial_balance_accounts",
        "import_runs",
        "client_group_tax_years",
    ):
        op.execute(f'DROP POLICY IF EXISTS tenant_isolation_policy_{table} ON {table}')
        op.execute(f'ALTER TABLE {table} DISABLE ROW LEVEL SECURITY')

    op.drop_index("idx_trial_balance_lines_account", table_name="trial_balance_lines")
    op.drop_index("idx_trial_balance_lines_snapshot", table_name="trial_balance_lines")
    op.drop_table("trial_balance_lines")

    op.drop_constraint("uq_trial_balance_snapshot", "trial_balance_snapshots", type_="unique")
    op.drop_index("idx_trial_balance_snapshots_entity_period", table_name="trial_balance_snapshots")
    op.drop_table("trial_balance_snapshots")

    op.drop_index("idx_trial_balance_accounts_entity", table_name="trial_balance_accounts")
    op.drop_table("trial_balance_accounts")

    op.drop_index("idx_import_runs_group", table_name="import_runs")
    op.drop_index("idx_import_runs_entity_year", table_name="import_runs")
    op.drop_index("idx_import_runs_tenant", table_name="import_runs")
    op.drop_table("import_runs")

    op.drop_constraint("uq_client_group_tax_year", "client_group_tax_years", type_="unique")
    op.drop_index("idx_client_group_tax_years_group", table_name="client_group_tax_years")
    op.drop_index("idx_client_group_tax_years_tenant", table_name="client_group_tax_years")
    op.drop_table("client_group_tax_years")

    op.drop_column("client_group_entities", "notes")
    op.drop_column("client_group_entities", "tags")
    op.drop_column("client_group_entities", "end_date")
    op.drop_column("client_group_entities", "start_date")
    op.drop_column("entities", "status")
    op.drop_column("entities", "entity_type")
