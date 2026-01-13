import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete, select

from app.api.v1.auth import get_current_user
from app.core.config import settings
from app.core.database import AsyncSessionLocal, set_tenant_context_async
from app.main import app
from app.models.client_group import ClientGroup, ClientGroupEntity, ClientGroupMembership
from app.models.entity import Entity
from app.models.role import Role
from app.models.tenant import Tenant, TenantMembership
from app.models.user import User


async def _get_or_create_role(session, slug: str, name: str) -> Role:
    result = await session.execute(select(Role).where(Role.slug == slug))
    role = result.scalar_one_or_none()
    if role:
        return role
    role = Role(slug=slug, name=name, is_system_role=True, is_default=False)
    session.add(role)
    await session.flush()
    return role


@pytest_asyncio.fixture
async def seeded_data():
    async with AsyncSessionLocal() as session:
        tenant_id = uuid.uuid4()
        tenant = Tenant(name="Test Tenant", slug=f"tenant-{tenant_id}")
        session.add(tenant)
        await session.flush()

        admin_user = User(email=f"admin-{tenant_id}@example.com", is_active=True, is_verified=True)
        client_user = User(email=f"client-{tenant_id}@example.com", is_active=True, is_verified=True)
        session.add_all([admin_user, client_user])
        await session.flush()

        admin_role = await _get_or_create_role(session, "admin", "Admin")
        client_role = await _get_or_create_role(session, "client", "Client")

        await set_tenant_context_async(session, str(tenant.id))
        session.add_all(
            [
                TenantMembership(
                    tenant_id=tenant.id,
                    user_id=admin_user.id,
                    role_id=admin_role.id,
                ),
                TenantMembership(
                    tenant_id=tenant.id,
                    user_id=client_user.id,
                    role_id=client_role.id,
                ),
            ]
        )
        await session.commit()

        yield {
            "tenant": tenant,
            "admin_user": admin_user,
            "client_user": client_user,
        }

        await set_tenant_context_async(session, str(tenant.id))
        await session.execute(delete(ClientGroupMembership).where(ClientGroupMembership.tenant_id == tenant.id))
        await session.execute(delete(ClientGroupEntity).where(ClientGroupEntity.tenant_id == tenant.id))
        await session.execute(delete(ClientGroup).where(ClientGroup.tenant_id == tenant.id))
        await session.execute(delete(Entity).where(Entity.tenant_id == tenant.id))
        await session.execute(delete(TenantMembership).where(TenantMembership.tenant_id == tenant.id))
        await session.execute(delete(Tenant).where(Tenant.id == tenant.id))
        await session.execute(delete(User).where(User.id.in_([admin_user.id, client_user.id])))
        await session.commit()


@pytest.mark.asyncio
async def test_client_group_membership_unique_for_client(seeded_data):
    tenant = seeded_data["tenant"]
    admin_user = seeded_data["admin_user"]
    client_user = seeded_data["client_user"]

    async def _override_user():
        return admin_user

    app.dependency_overrides[get_current_user] = _override_user

    headers = {settings.TENANT_HEADER_NAME: str(tenant.id)}
    async with AsyncClient(app=app, base_url="http://test") as client:
        create_resp = await client.post(
            f"{settings.API_V1_PREFIX}/client-groups/",
            json={"name": "Group One"},
            headers=headers,
        )
        assert create_resp.status_code == 201
        group_one_id = create_resp.json()["id"]

        create_resp = await client.post(
            f"{settings.API_V1_PREFIX}/client-groups/",
            json={"name": "Group Two"},
            headers=headers,
        )
        assert create_resp.status_code == 201
        group_two_id = create_resp.json()["id"]

        membership_resp = await client.post(
            f"{settings.API_V1_PREFIX}/client-groups/{group_one_id}/memberships",
            json={"user_id": str(client_user.id), "role_slug": "client"},
            headers=headers,
        )
        assert membership_resp.status_code == 200

        second_resp = await client.post(
            f"{settings.API_V1_PREFIX}/client-groups/{group_two_id}/memberships",
            json={"user_id": str(client_user.id), "role_slug": "client"},
            headers=headers,
        )
        assert second_resp.status_code == 409

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_visible_groups_and_entities_for_client(seeded_data):
    tenant = seeded_data["tenant"]
    admin_user = seeded_data["admin_user"]
    client_user = seeded_data["client_user"]

    async def _override_admin():
        return admin_user

    headers = {settings.TENANT_HEADER_NAME: str(tenant.id)}
    app.dependency_overrides[get_current_user] = _override_admin

    async with AsyncClient(app=app, base_url="http://test") as client:
        group_resp = await client.post(
            f"{settings.API_V1_PREFIX}/client-groups/",
            json={"name": "Visible Group"},
            headers=headers,
        )
        group_id = group_resp.json()["id"]

        entity_resp = await client.post(
            f"{settings.API_V1_PREFIX}/entities/",
            json={"name": "Entity One", "source_type": "MANUAL_PROFORMA"},
            headers=headers,
        )
        entity_id = entity_resp.json()["id"]

        assign_resp = await client.post(
            f"{settings.API_V1_PREFIX}/client-groups/{group_id}/entities",
            json={"entity_id": entity_id},
            headers=headers,
        )
        assert assign_resp.status_code == 201

        membership_resp = await client.post(
            f"{settings.API_V1_PREFIX}/client-groups/{group_id}/memberships",
            json={"user_id": str(client_user.id), "role_slug": "client"},
            headers=headers,
        )
        assert membership_resp.status_code == 200

    async def _override_client():
        return client_user

    app.dependency_overrides[get_current_user] = _override_client

    async with AsyncClient(app=app, base_url="http://test") as client:
        visible_groups = await client.get(
            f"{settings.API_V1_PREFIX}/client-groups/visible",
            headers=headers,
        )
        assert visible_groups.status_code == 200
        assert len(visible_groups.json()) == 1

        visible_entities = await client.get(
            f"{settings.API_V1_PREFIX}/client-groups/visible/entities",
            headers=headers,
        )
        assert visible_entities.status_code == 200
        assert entity_id in visible_entities.json()

    app.dependency_overrides.clear()
