"""
Tenant Middleware
Automatically identifies and sets tenant context for each request
"""
import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.tenant import tenant_context, tenant_identifier

logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to identify and set tenant context for each request
    Extracts tenant ID from subdomain or header and sets it in context
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and set tenant context"""

        # Skip tenant identification for certain paths
        excluded_paths = [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]

        if any(request.url.path.startswith(path) for path in excluded_paths):
            return await call_next(request)

        # Identify tenant from request
        tenant_id = tenant_identifier.from_request(request)

        # Set tenant context if identified
        if tenant_id:
            tenant_context.set(tenant_id)
            logger.debug(f"Tenant context set: {tenant_id}")

            # Add tenant ID to request state for easy access
            request.state.tenant_id = tenant_id
        else:
            # Clear tenant context
            tenant_context.clear()
            request.state.tenant_id = None

        try:
            # Process request
            response = await call_next(request)

            # Add tenant ID to response headers (for debugging)
            if tenant_id:
                response.headers["X-Tenant-ID"] = tenant_id

            return response

        finally:
            # Always clear tenant context after request
            tenant_context.clear()
