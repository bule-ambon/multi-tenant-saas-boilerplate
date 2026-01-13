"""Add client groups and entity memberships

Revision ID: 002
Revises: 001
Create Date: 2024-02-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create client group and entity membership tables"""
    op.create_table(
        "client_groups",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "tenant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_client_groups_tenant", "client_groups", ["tenant_id"])
    op.create_unique_constraint("uq_client_groups_tenant_name", "client_groups", ["tenant_id", "name"])

    op.create_table(
        "client_group_entities",
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
        sa.Column("entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_unique_constraint(
        "uq_client_group_entities",
        "client_group_entities",
        ["tenant_id", "client_group_id", "entity_id"],
    )
    op.create_index("idx_client_group_entities_group", "client_group_entities", ["client_group_id"])
    op.create_index("idx_client_group_entities_tenant", "client_group_entities", ["tenant_id"])
    op.create_index("idx_client_group_entities_entity", "client_group_entities", ["entity_id"])

    op.create_table(
        "client_group_memberships",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "tenant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "client_group_id",
            UUID(as_uuid=True),
            sa.ForeignKey("client_groups.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role_slug", sa.String(100), nullable=False, server_default="client"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_unique_constraint(
        "uq_client_group_membership",
        "client_group_memberships",
        ["tenant_id", "user_id", "client_group_id"],
    )
    op.create_index("idx_client_group_memberships_tenant", "client_group_memberships", ["tenant_id"])
    op.create_index("idx_client_group_memberships_group", "client_group_memberships", ["client_group_id"])
    op.create_index(
        "uq_client_group_memberships_client_user",
        "client_group_memberships",
        ["tenant_id", "user_id"],
        unique=True,
        postgresql_where=sa.text("role_slug = 'client'"),
    )

    op.create_table(
        "entity_memberships",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "tenant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_unique_constraint(
        "uq_entity_memberships_user_entity",
        "entity_memberships",
        ["tenant_id", "user_id", "entity_id"],
    )
    op.create_index("idx_entity_memberships_tenant", "entity_memberships", ["tenant_id"])
    op.create_index("idx_entity_memberships_user", "entity_memberships", ["user_id"])
    op.create_index("idx_entity_memberships_entity", "entity_memberships", ["entity_id"])


def downgrade() -> None:
    """Drop client group and entity membership tables"""
    op.drop_index("idx_entity_memberships_entity", table_name="entity_memberships")
    op.drop_index("idx_entity_memberships_user", table_name="entity_memberships")
    op.drop_index("idx_entity_memberships_tenant", table_name="entity_memberships")
    op.drop_constraint("uq_entity_memberships_user_entity", "entity_memberships", type_="unique")
    op.drop_table("entity_memberships")

    op.drop_index("uq_client_group_memberships_client_user", table_name="client_group_memberships")
    op.drop_index("idx_client_group_memberships_group", table_name="client_group_memberships")
    op.drop_index("idx_client_group_memberships_tenant", table_name="client_group_memberships")
    op.drop_constraint("uq_client_group_membership", "client_group_memberships", type_="unique")
    op.drop_table("client_group_memberships")

    op.drop_index("idx_client_group_entities_entity", table_name="client_group_entities")
    op.drop_index("idx_client_group_entities_tenant", table_name="client_group_entities")
    op.drop_index("idx_client_group_entities_group", table_name="client_group_entities")
    op.drop_constraint("uq_client_group_entities", "client_group_entities", type_="unique")
    op.drop_table("client_group_entities")

    op.drop_constraint("uq_client_groups_tenant_name", "client_groups", type_="unique")
    op.drop_index("idx_client_groups_tenant", table_name="client_groups")
    op.drop_table("client_groups")
