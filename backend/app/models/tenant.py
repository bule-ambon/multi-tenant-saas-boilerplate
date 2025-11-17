"""
Tenant Models
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Tenant(Base):
    """Tenant/Organization model"""

    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)  # URL-friendly identifier

    # Contact Information
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    website = Column(String(255), nullable=True)

    # Branding
    logo_url = Column(String(512), nullable=True)
    primary_color = Column(String(7), nullable=True)  # Hex color
    secondary_color = Column(String(7), nullable=True)

    # Custom Domain
    custom_domain = Column(String(255), nullable=True, unique=True, index=True)
    domain_verified = Column(Boolean, default=False, nullable=False)
    domain_verified_at = Column(DateTime(timezone=True), nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_suspended = Column(Boolean, default=False, nullable=False)
    suspended_at = Column(DateTime(timezone=True), nullable=True)
    suspended_reason = Column(Text, nullable=True)

    # Plan & Billing
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True)

    # Database mode (for isolated tenancy)
    database_name = Column(String(100), nullable=True)  # For database-per-tenant mode

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    memberships = relationship("TenantMembership", back_populates="tenant", cascade="all, delete-orphan")
    invitations = relationship("TenantInvitation", back_populates="tenant", cascade="all, delete-orphan")
    settings = relationship("TenantSettings", back_populates="tenant", uselist=False, cascade="all, delete-orphan")
    subscription = relationship("Subscription", foreign_keys=[subscription_id])
    roles = relationship("Role", back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tenant {self.name} ({self.slug})>"

    @property
    def is_trial(self) -> bool:
        """Check if tenant is in trial period"""
        if self.subscription:
            return self.subscription.is_trial
        return False

    @property
    def can_access(self) -> bool:
        """Check if tenant can access the platform"""
        return self.is_active and not self.is_suspended


class TenantMembership(Base):
    """User membership in tenants"""

    __tablename__ = "tenant_memberships"
    __table_args__ = (
        # Enable RLS for tenant isolation
        {"postgresql_enable_row_level_security": True},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Role within tenant (reference to tenant-specific roles)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="SET NULL"), nullable=True)

    # Membership Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_owner = Column(Boolean, default=False, nullable=False)  # Tenant owner/creator

    # Invitation tracking
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    invitation_accepted_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    joined_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    last_accessed_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="memberships")
    user = relationship("User", back_populates="tenant_memberships", foreign_keys=[user_id])
    role = relationship("Role")
    inviter = relationship("User", foreign_keys=[invited_by])

    def __repr__(self):
        return f"<TenantMembership {self.user_id} in {self.tenant_id}>"


class TenantInvitation(Base):
    """Pending invitations to join tenant"""

    __tablename__ = "tenant_invitations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    # Invitee Information
    email = Column(String(255), nullable=False, index=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="SET NULL"), nullable=True)

    # Invitation Token
    token = Column(String(255), unique=True, index=True, nullable=False)

    # Status
    is_accepted = Column(Boolean, default=False, nullable=False)
    is_expired = Column(Boolean, default=False, nullable=False)

    # Inviter
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="invitations")
    role = relationship("Role")
    inviter = relationship("User")

    def __repr__(self):
        return f"<TenantInvitation {self.email} to {self.tenant_id}>"


class TenantSettings(Base):
    """Tenant-specific settings and configuration"""

    __tablename__ = "tenant_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Feature Flags
    features_enabled = Column(JSON, nullable=True)  # {"feature_name": true/false}

    # Limits & Quotas
    max_users = Column(Integer, nullable=True)
    max_storage_gb = Column(Integer, nullable=True)
    max_api_calls_per_month = Column(Integer, nullable=True)

    # Notifications
    notification_email = Column(String(255), nullable=True)
    webhook_url = Column(String(512), nullable=True)
    webhook_secret = Column(String(255), nullable=True)

    # Security Settings
    require_mfa = Column(Boolean, default=False, nullable=False)
    allowed_ip_addresses = Column(JSON, nullable=True)  # List of allowed IPs
    session_timeout_minutes = Column(Integer, default=60, nullable=False)

    # Customization
    custom_css = Column(Text, nullable=True)
    custom_javascript = Column(Text, nullable=True)
    custom_metadata = Column(JSON, nullable=True)  # Additional custom fields

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    tenant = relationship("Tenant", back_populates="settings")

    def __repr__(self):
        return f"<TenantSettings {self.tenant_id}>"
