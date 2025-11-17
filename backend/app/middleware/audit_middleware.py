"""
Audit Middleware
Logs all important API requests for security and compliance
"""
import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

logger = logging.getLogger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware to audit API requests
    Logs request details, user information, and response status
    """

    def __init__(self, app):
        super().__init__(app)
        self.enabled = settings.ENABLE_AUDIT_LOGS

        # Paths that should be audited
        self.audit_paths = [
            "/api/v1/auth",
            "/api/v1/tenants",
            "/api/v1/users",
            "/api/v1/billing",
            "/api/v1/admin",
            "/api/v1/roles",
        ]

        # Methods that should be audited (write operations)
        self.audit_methods = ["POST", "PUT", "PATCH", "DELETE"]

    def should_audit(self, request: Request) -> bool:
        """Determine if request should be audited"""
        if not self.enabled:
            return False

        # Check if path should be audited
        if any(request.url.path.startswith(path) for path in self.audit_paths):
            return True

        # Check if method is a write operation
        if request.method in self.audit_methods:
            return True

        return False

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process and audit request"""

        # Start timer
        start_time = time.time()

        # Determine if we should audit this request
        should_audit = self.should_audit(request)

        # Extract request details
        tenant_id = getattr(request.state, "tenant_id", None)
        user_id = getattr(request.state, "user_id", None)  # Set by auth dependency
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")

        # Process request
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Log request if should be audited
        if should_audit:
            log_data = {
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "tenant_id": tenant_id,
                "user_id": user_id,
                "ip_address": ip_address,
                "user_agent": user_agent[:100],  # Truncate long user agents
                "process_time": f"{process_time:.3f}s",
            }

            # Log with appropriate level based on status code
            if response.status_code >= 500:
                logger.error(f"Audit log: {log_data}")
            elif response.status_code >= 400:
                logger.warning(f"Audit log: {log_data}")
            else:
                logger.info(f"Audit log: {log_data}")

            # TODO: Store audit log in database
            # This would involve creating AuditLog records in the database
            # For now, we just log to the application logger

        # Add processing time header
        response.headers["X-Process-Time"] = f"{process_time:.3f}"

        return response
