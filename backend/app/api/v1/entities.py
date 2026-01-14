"""
Entity API Routes
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.access import CLIENT_ROLE_SLUG, apply_entity_visibility, apply_tenant_filter, get_user_role_slug
from app.core.database import get_async_db
from app.core.tenant import require_tenant, tenant_validator
from app.models.entity import Entity
from app.models.user import User

router = APIRouter()


class EntityCreate(BaseModel):
    name: str
    entity_type: Optional[str] = "Individual"
    status: Optional[str] = "active"
    ein: Optional[str] = None
    tax_type: Optional[str] = None
    source_type: str = "MANUAL_PROFORMA"
    notes: Optional[str] = None


class EntityUpdate(BaseModel):
    name: Optional[str] = None
    entity_type: Optional[str] = None
    status: Optional[str] = None
    ein: Optional[str] = None
    tax_type: Optional[str] = None
    source_type: Optional[str] = None
    notes: Optional[str] = None


class EntityResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    entity_type: str
    status: str
    ein: Optional[str]
    tax_type: Optional[str]
    source_type: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


async def _require_non_client(db: AsyncSession, tenant_id: str, user_id: str):
    role_slug = await get_user_role_slug(db, tenant_id, user_id)
    if role_slug == CLIENT_ROLE_SLUG:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client role cannot modify entities",
        )


@router.get("/", response_model=List[EntityResponse])
async def list_entities(
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(require_tenant),
    db: AsyncSession = Depends(get_async_db),
):
    if not await tenant_validator.validate_tenant_access(tenant_id, str(current_user.id), db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    query = select(Entity)
    query = apply_tenant_filter(query, Entity, tenant_id)
    query = await apply_entity_visibility(query, Entity.id, tenant_id, str(current_user.id), db)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: UUID,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(require_tenant),
    db: AsyncSession = Depends(get_async_db),
):
    if not await tenant_validator.validate_tenant_access(tenant_id, str(current_user.id), db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    query = select(Entity).where(Entity.id == entity_id)
    query = apply_tenant_filter(query, Entity, tenant_id)
    query = await apply_entity_visibility(query, Entity.id, tenant_id, str(current_user.id), db)
    result = await db.execute(query)
    entity = result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")
    return entity


@router.post("/", response_model=EntityResponse, status_code=status.HTTP_201_CREATED)
async def create_entity(
    payload: EntityCreate,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(require_tenant),
    db: AsyncSession = Depends(get_async_db),
):
    if not await tenant_validator.validate_tenant_access(tenant_id, str(current_user.id), db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    await _require_non_client(db, tenant_id, str(current_user.id))

    entity = Entity(
        tenant_id=tenant_id,
        name=payload.name,
        entity_type=payload.entity_type,
        status=payload.status,
        ein=payload.ein,
        tax_type=payload.tax_type,
        source_type=payload.source_type,
        notes=payload.notes,
    )
    db.add(entity)
    await db.commit()
    await db.refresh(entity)
    return entity


@router.put("/{entity_id}", response_model=EntityResponse)
async def update_entity(
    entity_id: UUID,
    payload: EntityUpdate,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(require_tenant),
    db: AsyncSession = Depends(get_async_db),
):
    if not await tenant_validator.validate_tenant_access(tenant_id, str(current_user.id), db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    await _require_non_client(db, tenant_id, str(current_user.id))

    query = select(Entity).where(Entity.id == entity_id)
    query = apply_tenant_filter(query, Entity, tenant_id)
    result = await db.execute(query)
    entity = result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(entity, field, value)

    await db.commit()
    await db.refresh(entity)
    return entity


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entity(
    entity_id: UUID,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(require_tenant),
    db: AsyncSession = Depends(get_async_db),
):
    if not await tenant_validator.validate_tenant_access(tenant_id, str(current_user.id), db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    await _require_non_client(db, tenant_id, str(current_user.id))

    query = select(Entity).where(Entity.id == entity_id)
    query = apply_tenant_filter(query, Entity, tenant_id)
    result = await db.execute(query)
    entity = result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")

    await db.delete(entity)
    await db.commit()
