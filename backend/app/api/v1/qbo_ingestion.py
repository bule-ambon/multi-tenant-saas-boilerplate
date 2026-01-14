"""
QBO ingestion endpoints for import run management
"""
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.access import (
    CLIENT_ROLE_SLUG,
    apply_entity_visibility,
    apply_tenant_filter,
    get_user_role_slug,
)
from app.core.database import get_async_db
from app.core.tenant import require_tenant, tenant_validator
from app.models.client_group import ClientGroup
from app.models.entity import Entity
from app.models.qbo_ingestion import ImportRun
from app.models.user import User
from app.services.qbo import QBOImportService
from app.tasks.qbo_import import process_qbo_import_run_task

router = APIRouter()


class ImportRunCreate(BaseModel):
    entity_id: UUID
    tax_year: int
    period_end_date: date
    client_group_id: Optional[UUID] = None


class ImportRunResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    entity_id: UUID
    client_group_id: Optional[UUID]
    client_group_tax_year_id: Optional[UUID]
    tax_year: int
    period_end_date: date
    status: str
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    error_text: Optional[str]
    triggered_by_user_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


async def _require_non_client(db: AsyncSession, tenant_id: str, user_id: str):
    role_slug = await get_user_role_slug(db, tenant_id, user_id)
    if role_slug == CLIENT_ROLE_SLUG:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client role cannot manage import runs",
        )


async def _require_tenant_access(db: AsyncSession, tenant_id: str, user_id: str):
    if not await tenant_validator.validate_tenant_access(tenant_id, user_id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


@router.post("/", response_model=ImportRunResponse, status_code=status.HTTP_201_CREATED)
async def create_import_run(
    payload: ImportRunCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(require_tenant),
    db: AsyncSession = Depends(get_async_db),
):
    await _require_tenant_access(db, tenant_id, str(current_user.id))
    await _require_non_client(db, tenant_id, str(current_user.id))

    entity_query = select(Entity).where(Entity.id == payload.entity_id)
    entity_query = apply_tenant_filter(entity_query, Entity, tenant_id)
    entity_query = await apply_entity_visibility(
        entity_query,
        Entity.id,
        tenant_id,
        str(current_user.id),
        db,
    )
    entity = (await db.execute(entity_query)).scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")

    client_group_id = payload.client_group_id
    if client_group_id:
        group = await db.execute(
            apply_tenant_filter(select(ClientGroup), ClientGroup, tenant_id)
            .where(ClientGroup.id == client_group_id)
        )
        if not group.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client group not found")

    tax_year_record = None
    if client_group_id:
        tax_year_record = await QBOImportService.ensure_client_group_tax_year(
            db,
            tenant_id,
            client_group_id,
            payload.tax_year,
        )

    run = ImportRun(
        tenant_id=tenant_id,
        entity_id=payload.entity_id,
        tax_year=payload.tax_year,
        period_end_date=payload.period_end_date,
        client_group_id=client_group_id,
        client_group_tax_year_id=getattr(tax_year_record, "id", None),
        triggered_by_user_id=current_user.id,
    )
    db.add(run)
    await db.flush()
    background_tasks.add_task(process_qbo_import_run_task.delay, str(run.id), tenant_id)
    await db.refresh(run)
    return run


@router.get("/", response_model=List[ImportRunResponse])
async def list_import_runs(
    entity_id: Optional[UUID] = Query(None),
    client_group_id: Optional[UUID] = Query(None),
    tax_year: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(require_tenant),
    db: AsyncSession = Depends(get_async_db),
):
    await _require_tenant_access(db, tenant_id, str(current_user.id))

    query = select(ImportRun)
    query = apply_tenant_filter(query, ImportRun, tenant_id)
    if entity_id:
        query = query.where(ImportRun.entity_id == entity_id)
    if client_group_id:
        query = query.where(ImportRun.client_group_id == client_group_id)
    if tax_year:
        query = query.where(ImportRun.tax_year == tax_year)
    query = await apply_entity_visibility(
        query,
        ImportRun.entity_id,
        tenant_id,
        str(current_user.id),
        db,
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{run_id}", response_model=ImportRunResponse)
async def get_import_run(
    run_id: UUID,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(require_tenant),
    db: AsyncSession = Depends(get_async_db),
):
    await _require_tenant_access(db, tenant_id, str(current_user.id))

    query = select(ImportRun).where(ImportRun.id == run_id)
    query = apply_tenant_filter(query, ImportRun, tenant_id)
    query = await apply_entity_visibility(
        query,
        ImportRun.entity_id,
        tenant_id,
        str(current_user.id),
        db,
    )
    run = (await db.execute(query)).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import run not found")
    return run
