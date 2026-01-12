"""
Audit Log Models
Track all critical actions for compliance and security
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class AuditLog(Base):
    """
    Comprehensive audit logging for all critical actions
    """

    __tablename__ = "audit_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Action Details
    action = Column(String(100), nullable=False, index=True)  # user.login, tenant.create, etc.
    resource_type = Column(String(50), nullable=True, index=True)  # user, tenant, subscription, etc.
    resource_id = Column(String(255), nullable=True)

    # Request Context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    request_method = Column(String(10), nullable=True)  # GET, POST, PUT, DELETE
    request_path = Column(String(512), nullable=True)

    # Status
    status = Column(String(20), nullable=False, index=True)  # success, failure, error
    status_code = Column(String(10), nullable=True)  # HTTP status code or custom code

    # Additional Data
    audit_metadata = Column("metadata", JSON, nullable=True)  # Additional context
    changes = Column(JSON, nullable=True)  # Before/after for updates
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<AuditLog {self.action} by {self.user_id}>"
