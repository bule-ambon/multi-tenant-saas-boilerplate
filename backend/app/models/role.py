"""
Role-Based Access Control (RBAC) Models
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.user import User


class Role(Base):
    """
    Roles are tenant-specific
    Each tenant can define custom roles with custom permissions
    """

    __tablename__ = "roles"
    __table_args__ = (
        # Ensure role names are unique within a tenant
        UniqueConstraint("tenant_id", "name", name="uq_tenant_role_name"),
        # Enable RLS for tenant isolation
        {"postgresql_enable_row_level_security": True},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    # tenant_id is nullable for platform-level roles (super admin)

    name = Column(String(100), nullable=False, index=True)
    slug = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # Role Type
    is_system_role = Column(Boolean, default=False, nullable=False)  # Built-in, non-deletable
    is_default = Column(Boolean, default=False, nullable=False)  # Assigned to new members by default

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    tenant = relationship("Tenant", back_populates="roles")
    permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Role {self.name} ({self.tenant_id})>"


class Permission(Base):
    """
    Granular permissions for resources and actions
    Permissions are global but can be scoped to tenants through roles
    """

    __tablename__ = "permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Permission identifier (e.g., "users:create", "billing:read")
    name = Column(String(100), unique=True, nullable=False, index=True)
    resource = Column(String(50), nullable=False, index=True)  # users, billing, content, etc.
    action = Column(String(50), nullable=False)  # create, read, update, delete, manage

    description = Column(Text, nullable=True)

    # Permission Category
    category = Column(String(50), nullable=True)  # admin, user_management, billing, etc.

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    role_permissions = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Permission {self.name}>"


class RolePermission(Base):
    """
    Many-to-many relationship between roles and permissions
    Allows fine-grained permission assignment to roles
    """

    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
        # Enable RLS for tenant isolation
        {"postgresql_enable_row_level_security": True},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Permission constraints (optional)
    # Can be used for conditional permissions or field-level access
    constraints = Column(Text, nullable=True)  # JSON string for complex rules

    # Timestamps
    granted_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission", back_populates="role_permissions")

    def __repr__(self):
        return f"<RolePermission {self.role_id}:{self.permission_id}>"


class UserRole(Base):
    """
    User role assignments within tenants
    Users can have different roles in different tenants
    """

    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", "tenant_id", name="uq_user_role_tenant"),
        # Enable RLS for tenant isolation
        {"postgresql_enable_row_level_security": True},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)

    # Assignment metadata
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Timestamps
    assigned_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # For temporary role assignments

    # Relationships
    user = relationship("User", back_populates="roles", foreign_keys=[user_id])
    role = relationship("Role", back_populates="user_roles")
    assigner = relationship("User", foreign_keys=[assigned_by])

    def __repr__(self):
        return f"<UserRole {self.user_id}:{self.role_id}>"

    @property
    def is_expired(self) -> bool:
        """Check if role assignment is expired"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False

    @property
    def is_active(self) -> bool:
        """Check if role assignment is currently active"""
        return not self.is_expired
