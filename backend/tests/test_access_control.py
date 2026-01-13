import pytest
from sqlalchemy import Column, MetaData, String, Table, select
from unittest.mock import AsyncMock

from app.core.access import (
    CLIENT_ROLE_SLUG,
    apply_client_group_visibility,
    apply_entity_visibility,
    apply_tenant_filter,
)
from app.core.tenant import TenantValidator
from app.models.client_group import ClientGroup
from app.models.tenant import TenantMembership


class _Result:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


@pytest.mark.asyncio
async def test_validate_tenant_access_true():
    db = AsyncMock()
    db.execute.return_value = _Result(object())
    assert await TenantValidator.validate_tenant_access("tenant", "user", db) is True


@pytest.mark.asyncio
async def test_validate_tenant_access_false():
    db = AsyncMock()
    db.execute.return_value = _Result(None)
    assert await TenantValidator.validate_tenant_access("tenant", "user", db) is False


@pytest.mark.asyncio
async def test_validate_tenant_exists_true():
    db = AsyncMock()
    db.execute.return_value = _Result(object())
    assert await TenantValidator.validate_tenant_exists("tenant", db) is True


@pytest.mark.asyncio
async def test_validate_tenant_exists_false():
    db = AsyncMock()
    db.execute.return_value = _Result(None)
    assert await TenantValidator.validate_tenant_exists("tenant", db) is False


@pytest.mark.asyncio
async def test_apply_client_group_visibility_client_filters():
    query = select(ClientGroup)
    filtered = await apply_client_group_visibility(
        query,
        tenant_id="tenant",
        user_id="user",
        db=None,
        role_slug=CLIENT_ROLE_SLUG,
    )
    sql = str(filtered)
    assert "client_group_memberships" in sql


@pytest.mark.asyncio
async def test_apply_client_group_visibility_admin_unfiltered():
    query = select(ClientGroup)
    filtered = await apply_client_group_visibility(
        query,
        tenant_id="tenant",
        user_id="user",
        db=None,
        role_slug="admin",
    )
    sql = str(filtered)
    assert "client_group_memberships" not in sql


@pytest.mark.asyncio
async def test_apply_entity_visibility_client_filters():
    metadata = MetaData()
    entities = Table(
        "entities",
        metadata,
        Column("id", String, primary_key=True),
        Column("tenant_id", String),
    )
    query = select(entities)
    filtered = await apply_entity_visibility(
        query,
        entity_id_column=entities.c.id,
        tenant_id="tenant",
        user_id="user",
        db=None,
        role_slug=CLIENT_ROLE_SLUG,
    )
    sql = str(filtered)
    assert "client_group_entities" in sql
    assert "entity_memberships" in sql


def test_apply_tenant_filter_adds_where():
    query = select(TenantMembership)
    filtered = apply_tenant_filter(query, TenantMembership, "tenant")
    sql = str(filtered)
    assert "tenant_memberships.tenant_id" in sql
