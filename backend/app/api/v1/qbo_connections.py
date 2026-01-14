"""
QBO Connection API Routes
"""
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.access import CLIENT_ROLE_SLUG, apply_entity_visibility, apply_tenant_filter, get_user_role_slug
from app.core.config import settings
from app.core.database import get_async_db, get_tenant_db
from app.core.tenant import require_tenant, tenant_validator
from app.models.entity import Entity, QBOConnection
from app.models.user import User
from app.services.qbo import QBOOAuthService, QBOStateError, QBOStateManager

router = APIRouter()


class QBOConnectionCreate(BaseModel):
    entity_id: UUID
    realm_id: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None


class QBOConnectionUpdate(BaseModel):
    realm_id: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None


class QBOConnectionResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    entity_id: UUID
    realm_id: str
    access_token: Optional[str]
    refresh_token: Optional[str]
    token_expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QBOOAuthInitiate(BaseModel):
    entity_id: UUID
    redirect_uri: Optional[str] = None
    next_url: Optional[str] = None


class QBOOAuthResponse(BaseModel):
    authorization_url: str


async def _require_non_client(db: AsyncSession, tenant_id: str, user_id: str):
    role_slug = await get_user_role_slug(db, tenant_id, user_id)
    if role_slug == CLIENT_ROLE_SLUG:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client role cannot modify QBO connections",
        )


@router.get("/", response_model=List[QBOConnectionResponse])
async def list_qbo_connections(
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(require_tenant),
    db: AsyncSession = Depends(get_async_db),
):
    if not await tenant_validator.validate_tenant_access(tenant_id, str(current_user.id), db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    query = select(QBOConnection).join(Entity, QBOConnection.entity_id == Entity.id)
    query = apply_tenant_filter(query, QBOConnection, tenant_id)
    query = await apply_entity_visibility(query, Entity.id, tenant_id, str(current_user.id), db)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{connection_id}", response_model=QBOConnectionResponse)
async def get_qbo_connection(
    connection_id: UUID,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(require_tenant),
    db: AsyncSession = Depends(get_async_db),
):
    if not await tenant_validator.validate_tenant_access(tenant_id, str(current_user.id), db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    query = select(QBOConnection).where(QBOConnection.id == connection_id).join(Entity)
    query = apply_tenant_filter(query, QBOConnection, tenant_id)
    query = await apply_entity_visibility(query, Entity.id, tenant_id, str(current_user.id), db)
    result = await db.execute(query)
    connection = result.scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QBO connection not found")
    return connection


@router.post("/", response_model=QBOConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_qbo_connection(
    payload: QBOConnectionCreate,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(require_tenant),
    db: AsyncSession = Depends(get_async_db),
):
    if not await tenant_validator.validate_tenant_access(tenant_id, str(current_user.id), db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    await _require_non_client(db, tenant_id, str(current_user.id))

    entity_query = select(Entity).where(Entity.id == payload.entity_id)
    entity_query = apply_tenant_filter(entity_query, Entity, tenant_id)
    entity_result = await db.execute(entity_query)
    entity = entity_result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")

    existing = await db.execute(
        select(QBOConnection).where(QBOConnection.entity_id == payload.entity_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Entity already linked")

    realm_existing = await db.execute(
        select(QBOConnection).where(
            QBOConnection.tenant_id == tenant_id,
            QBOConnection.realm_id == payload.realm_id,
        )
    )
    if realm_existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Realm already linked")

    connection = QBOConnection(
        tenant_id=tenant_id,
        entity_id=payload.entity_id,
        realm_id=payload.realm_id,
        access_token=payload.access_token,
        refresh_token=payload.refresh_token,
        token_expires_at=payload.token_expires_at,
    )
    db.add(connection)
    await db.commit()
    await db.refresh(connection)
    return connection


@router.put("/{connection_id}", response_model=QBOConnectionResponse)
async def update_qbo_connection(
    connection_id: UUID,
    payload: QBOConnectionUpdate,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(require_tenant),
    db: AsyncSession = Depends(get_async_db),
):
    if not await tenant_validator.validate_tenant_access(tenant_id, str(current_user.id), db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    await _require_non_client(db, tenant_id, str(current_user.id))

    query = select(QBOConnection).where(QBOConnection.id == connection_id).join(Entity)
    query = apply_tenant_filter(query, QBOConnection, tenant_id)
    result = await db.execute(query)
    connection = result.scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QBO connection not found")

    if payload.realm_id and payload.realm_id != connection.realm_id:
        realm_existing = await db.execute(
            select(QBOConnection).where(
                QBOConnection.tenant_id == tenant_id,
                QBOConnection.realm_id == payload.realm_id,
            )
        )
        if realm_existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Realm already linked")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(connection, field, value)

    await db.commit()
    await db.refresh(connection)
    return connection


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_qbo_connection(
    connection_id: UUID,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(require_tenant),
    db: AsyncSession = Depends(get_async_db),
):
    if not await tenant_validator.validate_tenant_access(tenant_id, str(current_user.id), db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    await _require_non_client(db, tenant_id, str(current_user.id))

    query = select(QBOConnection).where(QBOConnection.id == connection_id)
    query = apply_tenant_filter(query, QBOConnection, tenant_id)
    result = await db.execute(query)
    connection = result.scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QBO connection not found")

    await db.delete(connection)


@router.post("/oauth/initiate", response_model=QBOOAuthResponse)
async def initiate_qbo_oauth(
    payload: QBOOAuthInitiate,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(require_tenant),
    db: AsyncSession = Depends(get_async_db),
):
    if not await tenant_validator.validate_tenant_access(tenant_id, str(current_user.id), db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    await _require_non_client(db, tenant_id, str(current_user.id))

    query = select(Entity).where(Entity.id == payload.entity_id)
    query = apply_tenant_filter(query, Entity, tenant_id)
    query = await apply_entity_visibility(query, Entity.id, tenant_id, str(current_user.id), db)
    entity_result = await db.execute(query)
    entity = entity_result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")

    redirect_uri = payload.redirect_uri or settings.QBO_REDIRECT_URI
    if not settings.QBO_CLIENT_ID or not redirect_uri:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="QBO redirect configuration missing")

    state = QBOStateManager.encode(
        tenant_id=tenant_id,
        entity_id=str(entity.id),
        redirect_uri=redirect_uri,
        next_url=payload.next_url,
    )
    authorization_url = (
        httpx.URL(settings.QBO_AUTHORIZATION_URL)
        .include_query_params(
            client_id=settings.QBO_CLIENT_ID,
            redirect_uri=redirect_uri,
            response_type="code",
            scope=settings.qbo_scope_string,
            state=state,
        )
    )

    return QBOOAuthResponse(authorization_url=str(authorization_url))


@router.get("/oauth/callback")
async def qbo_oauth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    realmId: Optional[str] = None,
    error: Optional[str] = None,
):
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    if not code or not state or not realmId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing OAuth parameters")

    try:
        payload = QBOStateManager.decode(state)
    except QBOStateError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    tenant_id = payload.get("tenant_id")
    entity_id = payload.get("entity_id")
    redirect_uri = payload.get("redirect_uri") or settings.QBO_REDIRECT_URI
    if not tenant_id or not entity_id or not redirect_uri:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth state missing metadata")

    try:
        token_data = await QBOOAuthService.exchange_code(code, redirect_uri)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    expires_in = token_data.get("expires_in")
    token_expires_at = datetime.utcnow() + timedelta(seconds=int(expires_in)) if expires_in else None

    async with get_tenant_db(tenant_id=tenant_id) as db:
        existing = await db.execute(
            select(QBOConnection).where(QBOConnection.entity_id == entity_id)
        )
        connection = existing.scalar_one_or_none()

        realm_conflict = await db.execute(
            select(QBOConnection).where(
                QBOConnection.tenant_id == tenant_id,
                QBOConnection.realm_id == realmId,
                QBOConnection.entity_id != entity_id,
            )
        )
        if realm_conflict.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="QuickBooks company already linked to another entity",
            )

        if connection:
            connection.access_token = token_data["access_token"]
            connection.refresh_token = token_data.get("refresh_token")
            connection.token_expires_at = token_expires_at
            connection.realm_id = realmId
        else:
            if not tenant_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid tenant context")
            connection = QBOConnection(
                tenant_id=tenant_id,
                entity_id=entity_id,
                realm_id=realmId,
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token"),
                token_expires_at=token_expires_at,
            )
            db.add(connection)

    next_url = payload.get("next") or str(settings.FRONTEND_URL)
    return RedirectResponse(next_url)
