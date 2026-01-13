"""
Core Application Components
"""
from app.core.config import settings
from app.core.database import Base, get_async_db, get_db, init_db, close_db
from app.core.security import (
    password_manager,
    token_manager,
    mfa_manager,
    encryption_manager,
    api_key_manager,
    csrf_manager,
    password_validator,
)
from app.core.tenant import (
    tenant_context,
    tenant_identifier,
    get_current_tenant,
    require_tenant,
    get_optional_tenant,
)
from app.core.access import (
    apply_tenant_filter,
    apply_client_group_visibility,
    apply_entity_visibility,
    get_user_role_slug,
)

__all__ = [
    "settings",
    "Base",
    "get_async_db",
    "get_db",
    "init_db",
    "close_db",
    "password_manager",
    "token_manager",
    "mfa_manager",
    "encryption_manager",
    "api_key_manager",
    "csrf_manager",
    "password_validator",
    "tenant_context",
    "tenant_identifier",
    "get_current_tenant",
    "require_tenant",
    "get_optional_tenant",
    "apply_tenant_filter",
    "apply_client_group_visibility",
    "apply_entity_visibility",
    "get_user_role_slug",
]
