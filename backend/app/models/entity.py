"""
Entity and QBO Connection Models
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Entity(Base):
    """Tenant-scoped entity"""

    __tablename__ = "entities"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_entities_tenant_name"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    entity_type = Column(String(50), nullable=False, default="Individual")
    status = Column(String(50), nullable=False, default="active")
    ein = Column(String(20), nullable=True)
    tax_type = Column(String(50), nullable=True)
    source_type = Column(String(50), nullable=False, default="MANUAL_PROFORMA")
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    tenant = relationship("Tenant")
    qbo_connection = relationship(
        "QBOConnection",
        uselist=False,
        back_populates="entity",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Entity {self.name} ({self.tenant_id})>"


class QBOConnection(Base):
    """1:1 mapping between entity and QBO company (realm)"""

    __tablename__ = "qbo_connections"
    __table_args__ = (
        UniqueConstraint("tenant_id", "realm_id", name="uq_qbo_connections_tenant_realm"),
        UniqueConstraint("entity_id", name="uq_qbo_connections_entity"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_id = Column(
        UUID(as_uuid=True),
        ForeignKey("entities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    realm_id = Column(String(64), nullable=False)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    tenant = relationship("Tenant")
    entity = relationship("Entity", back_populates="qbo_connection")

    def __repr__(self) -> str:
        return f"<QBOConnection {self.entity_id}:{self.realm_id}>"
