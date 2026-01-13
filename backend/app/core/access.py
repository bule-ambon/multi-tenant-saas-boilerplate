"""
Tenant access and visibility helpers.
"""
from typing import Optional

from sqlalchemy import select, union

from app.models.client_group import ClientGroup, ClientGroupEntity, ClientGroupMembership, EntityMembership
from app.models.role import Role
from app.models.tenant import TenantMembership

CLIENT_ROLE_SLUG = "client"


def apply_tenant_filter(query, model, tenant_id: str):
    """Apply tenant_id filter for tenant-scoped tables."""
    return query.where(model.tenant_id == tenant_id)


async def get_user_role_slug(db, tenant_id: str, user_id: str) -> Optional[str]:
    """Fetch the user's role slug within a tenant."""
    result = await db.execute(
        select(Role.slug)
        .join(TenantMembership, TenantMembership.role_id == Role.id)
        .where(
            TenantMembership.tenant_id == tenant_id,
            TenantMembership.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def apply_client_group_visibility(query, tenant_id: str, user_id: str, db, role_slug: Optional[str] = None):
    """
    Restrict client group visibility for client users.
    Non-client users see all tenant groups.
    """
    if role_slug is None:
        role_slug = await get_user_role_slug(db, tenant_id, user_id)

    if role_slug != CLIENT_ROLE_SLUG:
        return query

    membership_subquery = select(ClientGroupMembership.client_group_id).where(
        ClientGroupMembership.tenant_id == tenant_id,
        ClientGroupMembership.user_id == user_id,
    )
    return query.where(ClientGroup.id.in_(membership_subquery))


async def apply_entity_visibility(
    query,
    entity_id_column,
    tenant_id: str,
    user_id: str,
    db,
    role_slug: Optional[str] = None,
):
    """
    Restrict entity visibility for client users to group and direct memberships.
    """
    if role_slug is None:
        role_slug = await get_user_role_slug(db, tenant_id, user_id)

    if role_slug != CLIENT_ROLE_SLUG:
        return query

    group_entity_ids = (
        select(ClientGroupEntity.entity_id)
        .join(
            ClientGroupMembership,
            ClientGroupMembership.client_group_id == ClientGroupEntity.client_group_id,
        )
        .where(
            ClientGroupMembership.tenant_id == tenant_id,
            ClientGroupMembership.user_id == user_id,
        )
    )
    direct_entity_ids = select(EntityMembership.entity_id).where(
        EntityMembership.tenant_id == tenant_id,
        EntityMembership.user_id == user_id,
    )
    entity_union = union(group_entity_ids, direct_entity_ids).subquery()
    return query.where(entity_id_column.in_(select(entity_union.c.entity_id)))
