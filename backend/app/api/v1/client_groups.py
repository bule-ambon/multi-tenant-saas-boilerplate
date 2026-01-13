"""
Client Group API Routes
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.access import (
    CLIENT_ROLE_SLUG,
    apply_client_group_visibility,
    apply_entity_visibility,
    apply_tenant_filter,
    get_user_role_slug,
)
from app.core.database import get_async_db
from app.core.tenant import require_tenant, tenant_validator
from app.models.client_group import ClientGroup, ClientGroupEntity, ClientGroupMembership
from app.models.entity import Entity
from app.models.user import User

router = APIRouter()


class ClientGroupCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ClientGroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ClientGroupResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ClientGroupEntityCreate(BaseModel):
    entity_id: UUID


class ClientGroupMembershipCreate(BaseModel):
    user_id: UUID
    role_slug: str = CLIENT_ROLE_SLUG


class ClientGroupMembershipResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    user_id: UUID
    client_group_id: UUID
    role_slug: str
    created_at: datetime

    class Config:
        from_attributes = True


async def _require_non_client(db: AsyncSession, tenant_id: str, user_id: str):
    role_slug = await get_user_role_slug(db, tenant_id, user_id)
    if role_slug == CLIENT_ROLE_SLUG:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client role cannot modify client groups",
        )


async def _require_tenant_access(db: AsyncSession, tenant_id: str, user_id: str):
    if not await tenant_validator.validate_tenant_access(tenant_id, user_id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


@router.get("/", response_model=List[ClientGroupResponse])
async def list_client_groups(
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(require_tenant),
    db: AsyncSession = Depends(get_async_db),
):
    await _require_tenant_access(db, tenant_id, str(current_user.id))
    role_slug = await get_user_role_slug(db, tenant_id, str(current_user.id))

    query = select(ClientGroup)
    query = apply_tenant_filter(query, ClientGroup, tenant_id)
    query = await apply_client_group_visibility(
        query,
        tenant_id,
        str(current_user.id),
        db,
        role_slug=role_slug,
    )

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/visible/entities", response_model=List[UUID])
async def list_visible_entity_ids(
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(require_tenant),
    db: AsyncSession = Depends(get_async_db),
):
    await _require_tenant_access(db, tenant_id, str(current_user.id))

    query = select(Entity.id)
    query = apply_tenant_filter(query, Entity, tenant_id)
    query = await apply_entity_visibility(query, Entity.id, tenant_id, str(current_user.id), db)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/visible", response_model=List[ClientGroupResponse])
async def list_visible_groups(
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(require_tenant),
    db: AsyncSession = Depends(get_async_db),
):
    await _require_tenant_access(db, tenant_id, str(current_user.id))

    query = select(ClientGroup)
    query = apply_tenant_filter(query, ClientGroup, tenant_id)
    query = await apply_client_group_visibility(query, tenant_id, str(current_user.id), db)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{group_id}", response_model=ClientGroupResponse)
async def get_client_group(
    group_id: UUID,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(require_tenant),
    db: AsyncSession = Depends(get_async_db),
):
    await _require_tenant_access(db, tenant_id, str(current_user.id))
    role_slug = await get_user_role_slug(db, tenant_id, str(current_user.id))

    query = select(ClientGroup).where(ClientGroup.id == group_id)
    query = apply_tenant_filter(query, ClientGroup, tenant_id)
    query = await apply_client_group_visibility(
        query,
        tenant_id,
        str(current_user.id),
        db,
        role_slug=role_slug,
    )
    result = await db.execute(query)
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client group not found")
    return group


@router.post("/", response_model=ClientGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_client_group(
    payload: ClientGroupCreate,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(require_tenant),
    db: AsyncSession = Depends(get_async_db),
):
    await _require_tenant_access(db, tenant_id, str(current_user.id))
    await _require_non_client(db, tenant_id, str(current_user.id))

    group = ClientGroup(
        tenant_id=tenant_id,
        name=payload.name,
        description=payload.description,
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


@router.put("/{group_id}", response_model=ClientGroupResponse)
async def update_client_group(
    group_id: UUID,
    payload: ClientGroupUpdate,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(require_tenant),
    db: AsyncSession = Depends(get_async_db),
):
    await _require_tenant_access(db, tenant_id, str(current_user.id))
    await _require_non_client(db, tenant_id, str(current_user.id))

    query = select(ClientGroup).where(ClientGroup.id == group_id)
    query = apply_tenant_filter(query, ClientGroup, tenant_id)
    result = await db.execute(query)
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client group not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(group, field, value)

    await db.commit()
    await db.refresh(group)
    return group


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client_group(
    group_id: UUID,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(require_tenant),
    db: AsyncSession = Depends(get_async_db),
):
    await _require_tenant_access(db, tenant_id, str(current_user.id))
    await _require_non_client(db, tenant_id, str(current_user.id))

    query = select(ClientGroup).where(ClientGroup.id == group_id)
    query = apply_tenant_filter(query, ClientGroup, tenant_id)
    result = await db.execute(query)
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client group not found")

    await db.delete(group)
    await db.commit()


@router.post("/{group_id}/entities", status_code=status.HTTP_201_CREATED)
async def add_entity_to_group(
    group_id: UUID,
    payload: ClientGroupEntityCreate,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(require_tenant),
    db: AsyncSession = Depends(get_async_db),
):
    await _require_tenant_access(db, tenant_id, str(current_user.id))
    await _require_non_client(db, tenant_id, str(current_user.id))

    group_query = select(ClientGroup).where(ClientGroup.id == group_id)
    group_query = apply_tenant_filter(group_query, ClientGroup, tenant_id)
    group_result = await db.execute(group_query)
    group = group_result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client group not found")

    entity_query = select(Entity).where(Entity.id == payload.entity_id)
    entity_query = apply_tenant_filter(entity_query, Entity, tenant_id)
    entity_result = await db.execute(entity_query)
    entity = entity_result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")

    existing = await db.execute(
        select(ClientGroupEntity).where(
            ClientGroupEntity.tenant_id == tenant_id,
            ClientGroupEntity.client_group_id == group_id,
            ClientGroupEntity.entity_id == payload.entity_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Entity already assigned")

    assignment = ClientGroupEntity(
        tenant_id=tenant_id,
        client_group_id=group_id,
        entity_id=payload.entity_id,
    )
    db.add(assignment)
    await db.commit()
    return {"message": "Entity assigned"}


@router.delete("/{group_id}/entities/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_entity_from_group(
    group_id: UUID,
    entity_id: UUID,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(require_tenant),
    db: AsyncSession = Depends(get_async_db),
):
    await _require_tenant_access(db, tenant_id, str(current_user.id))
    await _require_non_client(db, tenant_id, str(current_user.id))

    result = await db.execute(
        select(ClientGroupEntity).where(
            ClientGroupEntity.tenant_id == tenant_id,
            ClientGroupEntity.client_group_id == group_id,
            ClientGroupEntity.entity_id == entity_id,
        )
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    await db.delete(assignment)
    await db.commit()


@router.post("/{group_id}/memberships", response_model=ClientGroupMembershipResponse)
async def add_member_to_group(
    group_id: UUID,
    payload: ClientGroupMembershipCreate,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(require_tenant),
    db: AsyncSession = Depends(get_async_db),
):
    await _require_tenant_access(db, tenant_id, str(current_user.id))
    await _require_non_client(db, tenant_id, str(current_user.id))

    group_query = select(ClientGroup).where(ClientGroup.id == group_id)
    group_query = apply_tenant_filter(group_query, ClientGroup, tenant_id)
    group_result = await db.execute(group_query)
    group = group_result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client group not found")

    membership = ClientGroupMembership(
        tenant_id=tenant_id,
        client_group_id=group_id,
        user_id=payload.user_id,
        role_slug=payload.role_slug,
    )
    db.add(membership)
    try:
        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Membership violates client group constraints",
        ) from exc
    await db.refresh(membership)
    return membership


@router.delete("/{group_id}/memberships/{membership_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member_from_group(
    group_id: UUID,
    membership_id: UUID,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(require_tenant),
    db: AsyncSession = Depends(get_async_db),
):
    await _require_tenant_access(db, tenant_id, str(current_user.id))
    await _require_non_client(db, tenant_id, str(current_user.id))

    result = await db.execute(
        select(ClientGroupMembership).where(
            ClientGroupMembership.tenant_id == tenant_id,
            ClientGroupMembership.client_group_id == group_id,
            ClientGroupMembership.id == membership_id,
        )
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")

    await db.delete(membership)
    await db.commit()
