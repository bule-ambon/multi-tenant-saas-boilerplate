"""Add entities and QBO connections

Revision ID: 004
Revises: 003
Create Date: 2024-02-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

# revision identifiers, used by Alembic.
revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create entities and QBO connections"""
    op.create_table(
        "entities",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "tenant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("ein", sa.String(20), nullable=True),
        sa.Column("tax_type", sa.String(50), nullable=True),
        sa.Column("source_type", sa.String(50), nullable=False, server_default="MANUAL_PROFORMA"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_entities_tenant", "entities", ["tenant_id"])
    op.create_unique_constraint("uq_entities_tenant_name", "entities", ["tenant_id", "name"])

    op.create_table(
        "qbo_connections",
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
        sa.Column("realm_id", sa.String(64), nullable=False),
        sa.Column("access_token", sa.Text, nullable=True),
        sa.Column("refresh_token", sa.Text, nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_qbo_connections_tenant", "qbo_connections", ["tenant_id"])
    op.create_unique_constraint("uq_qbo_connections_tenant_realm", "qbo_connections", ["tenant_id", "realm_id"])
    op.create_unique_constraint("uq_qbo_connections_entity", "qbo_connections", ["entity_id"])

    op.execute('ALTER TABLE entities ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE qbo_connections ENABLE ROW LEVEL SECURITY')

    op.execute("""
        CREATE POLICY tenant_isolation_policy_entities ON entities
        FOR ALL
        USING (tenant_id::text = current_setting('app.current_tenant_id', true))
    """)

    op.execute("""
        CREATE POLICY tenant_isolation_policy_qbo_connections ON qbo_connections
        FOR ALL
        USING (tenant_id::text = current_setting('app.current_tenant_id', true))
    """)


def downgrade() -> None:
    """Drop entities and QBO connections"""
    op.execute('DROP POLICY IF EXISTS tenant_isolation_policy_qbo_connections ON qbo_connections')
    op.execute('DROP POLICY IF EXISTS tenant_isolation_policy_entities ON entities')

    op.execute('ALTER TABLE qbo_connections DISABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE entities DISABLE ROW LEVEL SECURITY')

    op.drop_constraint("uq_qbo_connections_entity", "qbo_connections", type_="unique")
    op.drop_constraint("uq_qbo_connections_tenant_realm", "qbo_connections", type_="unique")
    op.drop_index("idx_qbo_connections_tenant", table_name="qbo_connections")
    op.drop_table("qbo_connections")

    op.drop_constraint("uq_entities_tenant_name", "entities", type_="unique")
    op.drop_index("idx_entities_tenant", table_name="entities")
    op.drop_table("entities")
