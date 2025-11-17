"""
Super Admin API Routes
Platform-level administration
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_async_db
from app.models.user import User
from app.models.tenant import Tenant
from app.api.v1.auth import get_current_user

router = APIRouter()


async def require_superuser(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to require superuser access"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required",
        )
    return current_user


@router.get("/tenants")
async def list_all_tenants(
    admin: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_async_db),
):
    """List all tenants in the system"""
    result = await db.execute(select(Tenant))
    tenants = result.scalars().all()

    return {
        "total": len(tenants),
        "tenants": [
            {
                "id": str(t.id),
                "name": t.name,
                "slug": t.slug,
                "is_active": t.is_active,
                "is_suspended": t.is_suspended,
                "created_at": t.created_at,
            }
            for t in tenants
        ],
    }


@router.post("/tenants/{tenant_id}/suspend")
async def suspend_tenant(
    tenant_id: str,
    reason: str,
    admin: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_async_db),
):
    """Suspend a tenant"""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    tenant.is_suspended = True
    tenant.suspended_reason = reason

    await db.commit()

    return {"message": f"Tenant {tenant.name} suspended"}


@router.get("/users")
async def list_all_users(
    admin: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_async_db),
):
    """List all users in the system"""
    result = await db.execute(select(User))
    users = result.scalars().all()

    return {
        "total": len(users),
        "users": [
            {
                "id": str(u.id),
                "email": u.email,
                "is_active": u.is_active,
                "is_verified": u.is_verified,
                "created_at": u.created_at,
            }
            for u in users
        ],
    }


@router.get("/stats")
async def get_platform_stats(
    admin: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_async_db),
):
    """Get platform statistics"""
    # Count tenants
    tenant_result = await db.execute(select(Tenant))
    total_tenants = len(tenant_result.scalars().all())

    # Count users
    user_result = await db.execute(select(User))
    total_users = len(user_result.scalars().all())

    return {
        "total_tenants": total_tenants,
        "total_users": total_users,
        "active_tenants": total_tenants,  # TODO: Filter active
        "active_users": total_users,  # TODO: Filter active
    }
