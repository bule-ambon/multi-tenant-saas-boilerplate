"""
API V1 Routes
"""
from fastapi import APIRouter

from app.api.v1 import auth, tenants, users, roles, billing, admin, entities, qbo_connections, client_groups

api_router = APIRouter()

# Include all route modules
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["Tenants"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(roles.router, prefix="/roles", tags=["Roles & Permissions"])
api_router.include_router(billing.router, prefix="/billing", tags=["Billing & Subscriptions"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_router.include_router(entities.router, prefix="/entities", tags=["Entities"])
api_router.include_router(qbo_connections.router, prefix="/qbo-connections", tags=["QBO Connections"])
api_router.include_router(client_groups.router, prefix="/client-groups", tags=["Client Groups"])

__all__ = ["api_router"]
