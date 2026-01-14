"""
QuickBooks Online integration helpers
"""
import base64
import hashlib
import hmac
import json
import time
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_tenant_db
from app.models.entity import QBOConnection
from app.models.qbo_ingestion import (
    ClientGroupTaxYear,
    ImportRun,
    TrialBalanceAccount,
    TrialBalanceLine,
    TrialBalanceSnapshot,
)


class QBOError(Exception):
    """Base exception for QBO helpers"""


class QBORateLimitExceeded(QBOError):
    """Raised when QuickBooks throttles requests"""


class QBOStateError(QBOError):
    """Raised when OAuth state is invalid"""


class QBOStateManager:
    """Encode/decode quick access state for OAuth flows"""

    TTL_SECONDS = 600

    @staticmethod
    def encode(
        tenant_id: str,
        entity_id: str,
        redirect_uri: str,
        next_url: Optional[str] = None,
    ) -> str:
        payload = {
            "tenant_id": tenant_id,
            "entity_id": entity_id,
            "redirect_uri": redirect_uri,
            "ts": int(time.time()),
        }
        if next_url:
            payload["next"] = next_url
        signature = QBOStateManager._signature(payload)
        payload["sig"] = signature
        encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
        return encoded

    @staticmethod
    def decode(raw_state: str) -> Dict[str, Any]:
        try:
            decoded = base64.urlsafe_b64decode(raw_state.encode()).decode()
            payload = json.loads(decoded)
        except (ValueError, json.JSONDecodeError):
            raise QBOStateError("Invalid OAuth state")

        signature = payload.pop("sig", None)
        if not signature or signature != QBOStateManager._signature(payload):
            raise QBOStateError("Invalid OAuth state signature")

        ts = payload.get("ts")
        if not isinstance(ts, int) or abs(int(time.time()) - ts) > QBOStateManager.TTL_SECONDS:
            raise QBOStateError("OAuth state expired")

        return payload

    @staticmethod
    def _signature(payload: Dict[str, Any]) -> str:
        signer = hmac.new(
            settings.SECRET_KEY.encode(),
            msg=f"{payload.get('tenant_id')}|{payload.get('entity_id')}|{payload.get('ts')}".encode(),
            digestmod=hashlib.sha256,
        )
        return signer.hexdigest()


class QBOOAuthService:
    """Handles token exchange and refresh for QuickBooks OAuth"""

    @staticmethod
    async def exchange_code(code: str, redirect_uri: str) -> Dict[str, Any]:
        if not settings.QBO_CLIENT_ID or not settings.QBO_CLIENT_SECRET:
            raise QBOError("QBO client credentials are not configured")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                settings.QBO_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
                auth=(settings.QBO_CLIENT_ID, settings.QBO_CLIENT_SECRET),
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def refresh_token(refresh_token: str) -> Dict[str, Any]:
        if not settings.QBO_CLIENT_ID or not settings.QBO_CLIENT_SECRET:
            raise QBOError("QBO client credentials are not configured")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                settings.QBO_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
                auth=(settings.QBO_CLIENT_ID, settings.QBO_CLIENT_SECRET),
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            return response.json()


class QBOClient:
    """HTTP client for QuickBooks Company APIs"""

    def __init__(self, access_token: str, realm_id: str):
        self._base_url = f"{settings.QBO_API_BASE_URL.rstrip('/')}/v3/company/{realm_id}"
        self._headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }

    async def fetch_trial_balance(self, tax_year: int, period_end_date: date) -> List[Dict[str, Any]]:
        params = {
            "start_date": f"{tax_year}-01-01",
            "end_date": period_end_date.isoformat(),
            "minorversion": "65",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self._base_url}/reports/TrialBalance", params=params, headers=self._headers)
            if response.status_code == 429:
                raise QBORateLimitExceeded("QBO rate limit exceeded")
            response.raise_for_status()
            payload = response.json()
        rows = payload.get("Rows", {}).get("Row") or []
        if isinstance(rows, dict):
            rows = [rows]
        snapshots: List[Dict[str, Any]] = []
        for row in rows:
            col_data = row.get("ColData") or []
            if not col_data or len(col_data) < 2:
                continue
            account_name = col_data[0].get("value")
            if not account_name or account_name.lower().startswith("total"):
                continue
            amount_raw = col_data[-1].get("value")
            amount = _parse_amount(amount_raw)
            snapshots.append(
                {
                    "account_name": account_name,
                    "amount": amount,
                    "external_account_id": row.get("account", {}).get("id"),
                    "account_type": row.get("account", {}).get("accountType"),
                }
            )
        return snapshots


def _parse_amount(value: Optional[str]) -> Decimal:
    if not value:
        return Decimal("0")
    clean = value.replace(",", "").strip()
    if clean.startswith("(") and clean.endswith(")"):
        clean = f"-{clean[1:-1]}"
    try:
        return Decimal(clean)
    except (InvalidOperation, ValueError):
        return Decimal("0")


class QBOImportService:
    """Business logic for managing QBO import runs"""

    @staticmethod
    async def process_run(run_id: str, tenant_id: str) -> None:
        async with get_tenant_db(tenant_id=tenant_id) as db:
            run = await db.get(ImportRun, run_id)
            if not run:
                raise QBOError("Import run not found")
            run.status = "running"
            run.started_at = datetime.utcnow()
            run.finished_at = None

            result = await db.execute(
                select(QBOConnection).where(
                    QBOConnection.entity_id == run.entity_id,
                    QBOConnection.tenant_id == tenant_id,
                )
            )
            connection = result.scalar_one_or_none()
            if not connection:
                raise QBOError("QBO connection for entity not found")

            if connection.token_expires_at and connection.token_expires_at < datetime.utcnow():
                await QBOImportService._refresh_tokens(connection, db)

            try:
                await QBOImportService._write_snapshot(run, connection, db)
            except QBORateLimitExceeded:
                raise
            except Exception as exc:
                run.status = "failed"
                run.error_text = str(exc)
                run.finished_at = datetime.utcnow()
                return
            run.status = "success"
            run.finished_at = datetime.utcnow()
            run.error_text = None

    @staticmethod
    async def _refresh_tokens(connection: QBOConnection, db: AsyncSession):
        if not connection.refresh_token:
            raise QBOError("Missing refresh token")
        token_data = await QBOOAuthService.refresh_token(connection.refresh_token)
        connection.access_token = token_data["access_token"]
        connection.refresh_token = token_data.get("refresh_token", connection.refresh_token)
        expires_in = token_data.get("expires_in")
        if expires_in:
            connection.token_expires_at = datetime.utcnow() + timedelta(seconds=int(expires_in))

    @staticmethod
    async def _write_snapshot(run: ImportRun, connection: QBOConnection, db: AsyncSession):
        client = QBOClient(connection.access_token, connection.realm_id)
        lines = await client.fetch_trial_balance(run.tax_year, run.period_end_date)

        snapshot = TrialBalanceSnapshot(
            tenant_id=run.tenant_id,
            entity_id=run.entity_id,
            import_run_id=run.id,
            tax_year=run.tax_year,
            period_end_date=run.period_end_date,
        )
        db.add(snapshot)
        await db.flush()

        account_cache: Dict[str, TrialBalanceAccount] = {}
        for line_data in lines:
            key = line_data.get("external_account_id") or line_data["account_name"]
            account = account_cache.get(key)
            if not account:
                account = await QBOImportService._get_or_create_account(
                    db,
                    run.entity_id,
                    run.tenant_id,
                    line_data["account_name"],
                    line_data.get("external_account_id"),
                    line_data.get("account_type"),
                )
                account_cache[key] = account

            tb_line = TrialBalanceLine(
                tenant_id=run.tenant_id,
                snapshot_id=snapshot.id,
                account_id=account.id,
                amount=line_data["amount"],
            )
            db.add(tb_line)

    @staticmethod
    async def _get_or_create_account(
        db: AsyncSession,
        entity_id: str,
        tenant_id: str,
        name: str,
        external_account_id: Optional[str],
        account_type: Optional[str],
    ) -> TrialBalanceAccount:
        query = select(TrialBalanceAccount).where(
            TrialBalanceAccount.entity_id == entity_id,
            TrialBalanceAccount.tenant_id == tenant_id,
        )
        if external_account_id:
            query = query.where(TrialBalanceAccount.external_account_id == external_account_id)
        else:
            query = query.where(TrialBalanceAccount.name == name)
        result = await db.execute(query)
        account = result.scalar_one_or_none()
        if account:
            return account

        account = TrialBalanceAccount(
            tenant_id=tenant_id,
            entity_id=entity_id,
            name=name,
            external_account_id=external_account_id,
            account_type=account_type,
        )
        db.add(account)
        await db.flush()
        return account

    @staticmethod
    async def ensure_client_group_tax_year(
        db: AsyncSession,
        tenant_id: str,
        client_group_id: Optional[UUID],
        tax_year: int,
    ) -> Optional[ClientGroupTaxYear]:
        if not client_group_id:
            return None

        result = await db.execute(
            select(ClientGroupTaxYear).where(
                ClientGroupTaxYear.client_group_id == client_group_id,
                ClientGroupTaxYear.tax_year == tax_year,
            )
        )
        target = result.scalar_one_or_none()
        if target:
            return target

        target = ClientGroupTaxYear(
            tenant_id=tenant_id,
            client_group_id=client_group_id,
            tax_year=tax_year,
        )
        db.add(target)
        await db.flush()
        return target
