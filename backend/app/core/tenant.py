"""
Tenant Context Management
Handles tenant identification and context for multi-tenant operations
"""
from contextvars import ContextVar
import uuid
from typing import Optional
from urllib.parse import urlparse

from fastapi import Header, HTTPException, Request, status

from app.core.config import settings

# Context variable to store current tenant ID
current_tenant_id: ContextVar[Optional[str]] = ContextVar("current_tenant_id", default=None)


class TenantContext:
    """Manage tenant context throughout request lifecycle"""

    @staticmethod
    def get() -> Optional[str]:
        """Get current tenant ID from context"""
        return current_tenant_id.get()

    @staticmethod
    def set(tenant_id: str):
        """Set current tenant ID in context"""
        current_tenant_id.set(tenant_id)

    @staticmethod
    def clear():
        """Clear tenant context"""
        current_tenant_id.set(None)


class TenantIdentifier:
    """Identify tenant from request"""

    @staticmethod
    def from_header(request: Request) -> Optional[str]:
        """Extract tenant ID from header"""
        tenant_id = request.headers.get(settings.TENANT_HEADER_NAME)
        if not tenant_id:
            return None
        try:
            return str(uuid.UUID(tenant_id))
        except ValueError:
            return None

    @staticmethod
    def from_request(request: Request) -> Optional[str]:
        """
        Identify tenant from request based on configured method
        """
        return TenantIdentifier.from_header(request)


def _require_tenant_header(request: Request) -> str:
    tenant_id = request.headers.get(settings.TENANT_HEADER_NAME)
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant identification required. Please provide tenant UUID via header.",
        )
    try:
        return str(uuid.UUID(tenant_id))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tenant ID format. Expected UUID.",
        ) from exc


async def get_current_tenant(request: Request) -> Optional[str]:
    """
    Dependency to extract and validate tenant ID from request
    Use this in endpoints that require tenant context
    """
    tenant_id = TenantIdentifier.from_request(request)
    if tenant_id:
        TenantContext.set(tenant_id)

    return tenant_id


async def require_tenant(request: Request) -> str:
    """
    Dependency that requires a valid tenant context
    Raises 400 if no tenant is identified
    """
    tenant_id = _require_tenant_header(request)
    TenantContext.set(tenant_id)
    return tenant_id


async def get_optional_tenant(request: Request) -> Optional[str]:
    """
    Dependency for optional tenant context
    Returns None if no tenant is identified (doesn't raise error)
    """
    return await get_current_tenant(request)


class TenantValidator:
    """Validate tenant operations and permissions"""

    @staticmethod
    async def validate_tenant_access(tenant_id: str, user_id: str, db) -> bool:
        """
        Validate that user has access to tenant
        """
        from sqlalchemy import select, true

        from app.models.tenant import TenantMembership

        result = await db.execute(
            select(TenantMembership).where(
                TenantMembership.tenant_id == tenant_id,
                TenantMembership.user_id == user_id,
            )
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def validate_tenant_exists(tenant_id: str, db) -> bool:
        """
        Validate that tenant exists and is active
        """
        from sqlalchemy import select

        from app.models.tenant import Tenant

        result = await db.execute(
            select(Tenant).where(
                Tenant.id == tenant_id,
                Tenant.is_active.is_(true()),
            )
        )
        return result.scalar_one_or_none() is not None


class TenantUrlBuilder:
    """Build tenant-specific URLs"""

    @staticmethod
    def build_tenant_url(tenant_id: str, path: str = "", scheme: str = "https") -> str:
        """
        Build full URL for tenant
        Example: build_tenant_url("tenant1", "/dashboard") -> https://tenant1.app.com/dashboard
        """
        # Get base domain from frontend URL
        frontend_url = str(settings.FRONTEND_URL)
        parsed = urlparse(frontend_url)

        base_domain = parsed.netloc

        # Remove existing subdomain if present
        parts = base_domain.split(".")
        if len(parts) > 2:
            base_domain = ".".join(parts[-2:])

        # Build tenant URL
        tenant_url = f"{scheme}://{tenant_id}.{base_domain}{path}"

        return tenant_url

    @staticmethod
    def build_api_url(tenant_id: str, path: str = "", scheme: str = "https") -> str:
        """Build API URL for tenant"""
        # Similar to tenant URL but with api subdomain
        frontend_url = str(settings.FRONTEND_URL)
        parsed = urlparse(frontend_url)

        base_domain = parsed.netloc
        parts = base_domain.split(".")
        if len(parts) > 2:
            base_domain = ".".join(parts[-2:])

        api_url = f"{scheme}://api.{base_domain}{path}"

        return api_url


# Global instances
tenant_context = TenantContext()
tenant_identifier = TenantIdentifier()
tenant_validator = TenantValidator()
tenant_url_builder = TenantUrlBuilder()
