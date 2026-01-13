"""
Tenant Management API Routes
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_async_db
from app.core.tenant import require_tenant, tenant_validator
from app.models.tenant import Tenant, TenantMembership, TenantSettings
from app.models.user import User
from app.api.v1.auth import get_current_user

router = APIRouter()


# Schemas
class TenantCreate(BaseModel):
    name: str
    slug: str
    email: Optional[str] = None


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None


class TenantResponse(BaseModel):
    id: str
    name: str
    slug: str
    email: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class MemberResponse(BaseModel):
    user_id: str
    email: str
    full_name: Optional[str]
    is_owner: bool
    joined_at: datetime

    class Config:
        from_attributes = True


# Routes
@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Create a new tenant/organization"""

    # Check if slug is already taken
    result = await db.execute(select(Tenant).where(Tenant.slug == tenant_data.slug))
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant slug already exists",
        )

    # Create tenant
    new_tenant = Tenant(
        name=tenant_data.name,
        slug=tenant_data.slug,
        email=tenant_data.email,
    )

    db.add(new_tenant)
    await db.flush()

    # Add creator as owner
    membership = TenantMembership(
        tenant_id=new_tenant.id,
        user_id=current_user.id,
        is_owner=True,
    )

    db.add(membership)

    # Create default settings
    settings = TenantSettings(tenant_id=new_tenant.id)
    db.add(settings)

    await db.commit()
    await db.refresh(new_tenant)

    return new_tenant


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: UUID,
    current_user: User = Depends(get_current_user),
    tenant_header_id: str = Depends(require_tenant),
    db: AsyncSession = Depends(get_async_db),
):
    """Get tenant details"""
    if not current_user.is_superuser and str(tenant_id) != tenant_header_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant context does not match requested tenant",
        )

    if not await tenant_validator.validate_tenant_exists(str(tenant_id), db):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    # Check user is member
    result = await db.execute(
        select(TenantMembership).where(
            TenantMembership.tenant_id == tenant_id,
            TenantMembership.user_id == current_user.id,
        )
    )
    membership = result.scalar_one_or_none()

    if not membership and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return tenant


@router.get("/", response_model=List[TenantResponse])
async def list_my_tenants(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """List all tenants the current user is a member of"""

    result = await db.execute(
        select(Tenant)
        .join(TenantMembership)
        .where(TenantMembership.user_id == current_user.id)
    )
    tenants = result.scalars().all()

    return tenants


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: UUID,
    tenant_data: TenantUpdate,
    current_user: User = Depends(get_current_user),
    tenant_header_id: str = Depends(require_tenant),
    db: AsyncSession = Depends(get_async_db),
):
    """Update tenant details"""
    if not current_user.is_superuser and str(tenant_id) != tenant_header_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant context does not match requested tenant",
        )

    if not await tenant_validator.validate_tenant_access(str(tenant_id), str(current_user.id), db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    # Check if user is owner or admin
    # TODO: Implement proper RBAC check

    # Update fields
    for field, value in tenant_data.model_dump(exclude_unset=True).items():
        setattr(tenant, field, value)

    await db.commit()
    await db.refresh(tenant)

    return tenant


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: UUID,
    current_user: User = Depends(get_current_user),
    tenant_header_id: str = Depends(require_tenant),
    db: AsyncSession = Depends(get_async_db),
):
    """Delete tenant (only owner can delete)"""
    if not current_user.is_superuser and str(tenant_id) != tenant_header_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant context does not match requested tenant",
        )

    if not await tenant_validator.validate_tenant_access(str(tenant_id), str(current_user.id), db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    # Check if user is owner
    result = await db.execute(
        select(TenantMembership).where(
            TenantMembership.tenant_id == tenant_id,
            TenantMembership.user_id == current_user.id,
            TenantMembership.is_owner == True,
        )
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tenant owner can delete",
        )

    await db.delete(tenant)
    await db.commit()
