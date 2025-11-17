"""Initial schema with Row-Level Security

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial schema with RLS policies"""

    # Create extension for UUID support
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Users table
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('hashed_password', sa.String(255), nullable=True),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('avatar_url', sa.String(512), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('is_verified', sa.Boolean, default=False, nullable=False),
        sa.Column('is_superuser', sa.Boolean, default=False, nullable=False),
        sa.Column('oauth_provider', sa.String(50), nullable=True),
        sa.Column('oauth_id', sa.String(255), nullable=True),
        sa.Column('mfa_enabled', sa.Boolean, default=False, nullable=False),
        sa.Column('mfa_secret', sa.String(32), nullable=True),
        sa.Column('backup_codes', sa.Text, nullable=True),
        sa.Column('failed_login_attempts', sa.Integer, default=0, nullable=False),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login_ip', sa.String(45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Subscription Plans table
    op.create_table(
        'subscription_plans',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), default='USD', nullable=False),
        sa.Column('billing_interval', sa.String(20), default='monthly', nullable=False),
        sa.Column('trial_days', sa.Integer, default=0, nullable=False),
        sa.Column('features', sa.JSON, nullable=True),
        sa.Column('max_users', sa.Integer, nullable=True),
        sa.Column('max_storage_gb', sa.Integer, nullable=True),
        sa.Column('max_api_calls', sa.Integer, nullable=True),
        sa.Column('stripe_price_id', sa.String(255), nullable=True),
        sa.Column('stripe_product_id', sa.String(255), nullable=True),
        sa.Column('paystack_plan_code', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('is_public', sa.Boolean, default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )

    # Tenants table
    op.create_table(
        'tenants',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('website', sa.String(255), nullable=True),
        sa.Column('logo_url', sa.String(512), nullable=True),
        sa.Column('primary_color', sa.String(7), nullable=True),
        sa.Column('secondary_color', sa.String(7), nullable=True),
        sa.Column('custom_domain', sa.String(255), nullable=True, unique=True),
        sa.Column('domain_verified', sa.Boolean, default=False, nullable=False),
        sa.Column('domain_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('is_suspended', sa.Boolean, default=False, nullable=False),
        sa.Column('suspended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('suspended_reason', sa.Text, nullable=True),
        sa.Column('subscription_id', UUID(as_uuid=True), nullable=True),
        sa.Column('database_name', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('plan_id', UUID(as_uuid=True), sa.ForeignKey('subscription_plans.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(20), default='trialing', nullable=False),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancel_at_period_end', sa.Boolean, default=False, nullable=False),
        sa.Column('trial_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trial_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(255), unique=True, nullable=True),
        sa.Column('stripe_customer_id', sa.String(255), nullable=True),
        sa.Column('paystack_subscription_code', sa.String(255), nullable=True),
        sa.Column('paystack_customer_code', sa.String(255), nullable=True),
        sa.Column('canceled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancellation_reason', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )

    # Add foreign key from tenants to subscriptions
    op.create_foreign_key(
        'fk_tenants_subscription_id',
        'tenants', 'subscriptions',
        ['subscription_id'], ['id'],
        ondelete='SET NULL'
    )

    # Permissions table
    op.create_table(
        'permissions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
        sa.Column('resource', sa.String(50), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Roles table (tenant-specific)
    op.create_table(
        'roles',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('is_system_role', sa.Boolean, default=False, nullable=False),
        sa.Column('is_default', sa.Boolean, default=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )
    op.create_unique_constraint('uq_tenant_role_name', 'roles', ['tenant_id', 'name'])

    # Enable RLS on roles
    op.execute('ALTER TABLE roles ENABLE ROW LEVEL SECURITY')

    # Role Permissions junction table
    op.create_table(
        'role_permissions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('role_id', UUID(as_uuid=True), sa.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('permission_id', UUID(as_uuid=True), sa.ForeignKey('permissions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('constraints', sa.Text, nullable=True),
        sa.Column('granted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_unique_constraint('uq_role_permission', 'role_permissions', ['role_id', 'permission_id'])

    # Enable RLS on role_permissions
    op.execute('ALTER TABLE role_permissions ENABLE ROW LEVEL SECURITY')

    # Tenant Memberships table
    op.create_table(
        'tenant_memberships',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role_id', UUID(as_uuid=True), sa.ForeignKey('roles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('is_owner', sa.Boolean, default=False, nullable=False),
        sa.Column('invited_by', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('invitation_accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Enable RLS on tenant_memberships
    op.execute('ALTER TABLE tenant_memberships ENABLE ROW LEVEL SECURITY')

    # User Roles table
    op.create_table(
        'user_roles',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role_id', UUID(as_uuid=True), sa.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True),
        sa.Column('assigned_by', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint('uq_user_role_tenant', 'user_roles', ['user_id', 'role_id', 'tenant_id'])

    # Enable RLS on user_roles
    op.execute('ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY')

    # User Devices table
    op.create_table(
        'user_devices',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('device_name', sa.String(255), nullable=True),
        sa.Column('device_type', sa.String(50), nullable=True),
        sa.Column('browser', sa.String(100), nullable=True),
        sa.Column('os', sa.String(100), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('fingerprint', sa.String(255), nullable=True),
        sa.Column('is_trusted', sa.Boolean, default=False, nullable=False),
        sa.Column('trust_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('first_seen_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # User Sessions table
    op.create_table(
        'user_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('refresh_token_hash', sa.String(255), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('device_id', UUID(as_uuid=True), sa.ForeignKey('user_devices.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Tenant Settings table
    op.create_table(
        'tenant_settings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('features_enabled', sa.JSON, nullable=True),
        sa.Column('max_users', sa.Integer, nullable=True),
        sa.Column('max_storage_gb', sa.Integer, nullable=True),
        sa.Column('max_api_calls_per_month', sa.Integer, nullable=True),
        sa.Column('notification_email', sa.String(255), nullable=True),
        sa.Column('webhook_url', sa.String(512), nullable=True),
        sa.Column('webhook_secret', sa.String(255), nullable=True),
        sa.Column('require_mfa', sa.Boolean, default=False, nullable=False),
        sa.Column('allowed_ip_addresses', sa.JSON, nullable=True),
        sa.Column('session_timeout_minutes', sa.Integer, default=60, nullable=False),
        sa.Column('custom_css', sa.Text, nullable=True),
        sa.Column('custom_javascript', sa.Text, nullable=True),
        sa.Column('custom_metadata', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )

    # Tenant Invitations table
    op.create_table(
        'tenant_invitations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('role_id', UUID(as_uuid=True), sa.ForeignKey('roles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('token', sa.String(255), unique=True, nullable=False),
        sa.Column('is_accepted', sa.Boolean, default=False, nullable=False),
        sa.Column('is_expired', sa.Boolean, default=False, nullable=False),
        sa.Column('invited_by', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Audit Logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('resource_id', sa.String(255), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('request_method', sa.String(10), nullable=True),
        sa.Column('request_path', sa.String(512), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('status_code', sa.String(10), nullable=True),
        sa.Column('metadata', sa.JSON, nullable=True),
        sa.Column('changes', sa.JSON, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Enable RLS on audit_logs
    op.execute('ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY')

    # Create RLS policies for shared tenancy mode
    # These policies ensure that users can only access data from their own tenant

    # Policy for roles table
    op.execute("""
        CREATE POLICY tenant_isolation_policy_roles ON roles
        FOR ALL
        USING (
            tenant_id IS NULL  -- Platform-level roles
            OR tenant_id::text = current_setting('app.current_tenant_id', true)
        )
    """)

    # Policy for role_permissions table
    op.execute("""
        CREATE POLICY tenant_isolation_policy_role_permissions ON role_permissions
        FOR ALL
        USING (
            EXISTS (
                SELECT 1 FROM roles
                WHERE roles.id = role_permissions.role_id
                AND (roles.tenant_id IS NULL OR roles.tenant_id::text = current_setting('app.current_tenant_id', true))
            )
        )
    """)

    # Policy for tenant_memberships table
    op.execute("""
        CREATE POLICY tenant_isolation_policy_memberships ON tenant_memberships
        FOR ALL
        USING (tenant_id::text = current_setting('app.current_tenant_id', true))
    """)

    # Policy for user_roles table
    op.execute("""
        CREATE POLICY tenant_isolation_policy_user_roles ON user_roles
        FOR ALL
        USING (
            tenant_id IS NULL  -- Platform-level roles
            OR tenant_id::text = current_setting('app.current_tenant_id', true)
        )
    """)

    # Policy for audit_logs table
    op.execute("""
        CREATE POLICY tenant_isolation_policy_audit_logs ON audit_logs
        FOR ALL
        USING (
            tenant_id IS NULL  -- Platform-wide logs
            OR tenant_id::text = current_setting('app.current_tenant_id', true)
        )
    """)

    # Create indexes for performance
    op.create_index('idx_tenant_memberships_tenant_user', 'tenant_memberships', ['tenant_id', 'user_id'])
    op.create_index('idx_user_sessions_user_active', 'user_sessions', ['user_id', 'is_active'])
    op.create_index('idx_audit_logs_tenant_created', 'audit_logs', ['tenant_id', 'created_at'])
    op.create_index('idx_roles_tenant_slug', 'roles', ['tenant_id', 'slug'])


def downgrade() -> None:
    """Drop all tables and policies"""

    # Drop policies
    op.execute('DROP POLICY IF EXISTS tenant_isolation_policy_roles ON roles')
    op.execute('DROP POLICY IF EXISTS tenant_isolation_policy_role_permissions ON role_permissions')
    op.execute('DROP POLICY IF EXISTS tenant_isolation_policy_memberships ON tenant_memberships')
    op.execute('DROP POLICY IF EXISTS tenant_isolation_policy_user_roles ON user_roles')
    op.execute('DROP POLICY IF EXISTS tenant_isolation_policy_audit_logs ON audit_logs')

    # Drop tables in reverse order
    op.drop_table('audit_logs')
    op.drop_table('tenant_invitations')
    op.drop_table('tenant_settings')
    op.drop_table('user_sessions')
    op.drop_table('user_devices')
    op.drop_table('user_roles')
    op.drop_table('tenant_memberships')
    op.drop_table('role_permissions')
    op.drop_table('roles')
    op.drop_table('permissions')

    # Drop foreign key from tenants first
    op.drop_constraint('fk_tenants_subscription_id', 'tenants', type_='foreignkey')

    op.drop_table('subscriptions')
    op.drop_table('tenants')
    op.drop_table('subscription_plans')
    op.drop_table('users')
