"""
Client Group and Entity Membership Models
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ClientGroup(Base):
    """Tenant-scoped client engagement groups"""

    __tablename__ = "client_groups"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_client_groups_tenant_name"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    tenant = relationship("Tenant")
    entities = relationship(
        "ClientGroupEntity",
        cascade="all, delete-orphan",
    )
    memberships = relationship(
        "ClientGroupMembership",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ClientGroup {self.name} ({self.tenant_id})>"


class ClientGroupEntity(Base):
    """Join table for client groups and entities"""

    __tablename__ = "client_group_entities"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "client_group_id",
            "entity_id",
            name="uq_client_group_entities",
        ),
        Index("idx_client_group_entities_group", "client_group_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    client_group_id = Column(
        UUID(as_uuid=True),
        ForeignKey("client_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    client_group = relationship("ClientGroup")
    tenant = relationship("Tenant")

    def __repr__(self) -> str:
        return f"<ClientGroupEntity {self.client_group_id}:{self.entity_id}>"


class ClientGroupMembership(Base):
    """User membership in a client group"""

    __tablename__ = "client_group_memberships"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "user_id",
            "client_group_id",
            name="uq_client_group_membership",
        ),
        Index(
            "uq_client_group_memberships_client_user",
            "tenant_id",
            "user_id",
            unique=True,
            postgresql_where=text("role_slug = 'client'"),
        ),
        Index("idx_client_group_memberships_group", "client_group_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    client_group_id = Column(
        UUID(as_uuid=True),
        ForeignKey("client_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_slug = Column(String(100), nullable=False, default="client")

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user = relationship("User")
    client_group = relationship("ClientGroup")
    tenant = relationship("Tenant")

    def __repr__(self) -> str:
        return f"<ClientGroupMembership {self.user_id}:{self.client_group_id}>"


class EntityMembership(Base):
    """User access to entities (tenant-scoped)"""

    __tablename__ = "entity_memberships"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "user_id",
            "entity_id",
            name="uq_entity_memberships_user_entity",
        ),
        Index("idx_entity_memberships_entity", "entity_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user = relationship("User")
    tenant = relationship("Tenant")

    def __repr__(self) -> str:
        return f"<EntityMembership {self.user_id}:{self.entity_id}>"
