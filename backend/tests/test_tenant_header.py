import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.core.config import settings
from app.core.tenant import TenantIdentifier, require_tenant


def _make_request(header_value: str | None) -> Request:
    headers = []
    if header_value is not None:
        headers.append((settings.TENANT_HEADER_NAME.lower().encode(), header_value.encode()))
    scope = {
        "type": "http",
        "headers": headers,
    }
    return Request(scope)


def test_tenant_identifier_from_header_valid_uuid():
    request = _make_request("550e8400-e29b-41d4-a716-446655440000")
    assert TenantIdentifier.from_header(request) == "550e8400-e29b-41d4-a716-446655440000"


def test_tenant_identifier_from_header_invalid_uuid():
    request = _make_request("not-a-uuid")
    assert TenantIdentifier.from_header(request) is None


@pytest.mark.asyncio
async def test_require_tenant_missing_header():
    request = _make_request(None)
    with pytest.raises(HTTPException) as exc:
        await require_tenant(request)
    assert "Tenant identification required" in str(exc.value)
