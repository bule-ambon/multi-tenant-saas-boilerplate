"""
Roles & Permissions API Routes (RBAC)
"""
from fastapi import APIRouter, Depends
from app.models.user import User
from app.api.v1.auth import get_current_user

router = APIRouter()


@router.get("/")
async def list_roles(
    current_user: User = Depends(get_current_user),
):
    """List all roles in current tenant"""
    # TODO: Implement RBAC role listing
    return {"roles": []}


@router.post("/")
async def create_role(
    current_user: User = Depends(get_current_user),
):
    """Create new role"""
    # TODO: Implement role creation
    return {"message": "Role created"}
