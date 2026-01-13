"""Add RLS policies and role constraints for client groups

Revision ID: 003
Revises: 002
Create Date: 2024-02-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Enable RLS and tighten client role constraints"""
    op.create_unique_constraint("uq_roles_slug", "roles", ["slug"])
    op.create_foreign_key(
        "fk_client_group_memberships_role_slug",
        "client_group_memberships",
        "roles",
        ["role_slug"],
        ["slug"],
        ondelete="RESTRICT",
    )

    op.execute('ALTER TABLE client_groups ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE client_group_entities ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE client_group_memberships ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE entity_memberships ENABLE ROW LEVEL SECURITY')

    op.execute("""
        CREATE POLICY tenant_isolation_policy_client_groups ON client_groups
        FOR ALL
        USING (tenant_id::text = current_setting('app.current_tenant_id', true))
    """)

    op.execute("""
        CREATE POLICY tenant_isolation_policy_client_group_entities ON client_group_entities
        FOR ALL
        USING (tenant_id::text = current_setting('app.current_tenant_id', true))
    """)

    op.execute("""
        CREATE POLICY tenant_isolation_policy_client_group_memberships ON client_group_memberships
        FOR ALL
        USING (tenant_id::text = current_setting('app.current_tenant_id', true))
    """)

    op.execute("""
        CREATE POLICY tenant_isolation_policy_entity_memberships ON entity_memberships
        FOR ALL
        USING (tenant_id::text = current_setting('app.current_tenant_id', true))
    """)


def downgrade() -> None:
    """Drop client group RLS policies and role constraints"""
    op.execute('DROP POLICY IF EXISTS tenant_isolation_policy_entity_memberships ON entity_memberships')
    op.execute('DROP POLICY IF EXISTS tenant_isolation_policy_client_group_memberships ON client_group_memberships')
    op.execute('DROP POLICY IF EXISTS tenant_isolation_policy_client_group_entities ON client_group_entities')
    op.execute('DROP POLICY IF EXISTS tenant_isolation_policy_client_groups ON client_groups')

    op.execute('ALTER TABLE entity_memberships DISABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE client_group_memberships DISABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE client_group_entities DISABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE client_groups DISABLE ROW LEVEL SECURITY')

    op.drop_constraint(
        "fk_client_group_memberships_role_slug",
        "client_group_memberships",
        type_="foreignkey",
    )
    op.drop_constraint("uq_roles_slug", "roles", type_="unique")
