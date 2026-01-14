"""
QBO import run tasks
"""
import asyncio

from celery import Task

from app.core.celery_app import celery_app
from app.services.qbo import QBORateLimitExceeded, QBOImportService


@celery_app.task(bind=True, max_retries=5, default_retry_delay=60)
def process_qbo_import_run_task(self: Task, run_id: str, tenant_id: str) -> None:
    """
    Process a queued QBO import run in the background.
    Retries on rate limiting errors with exponential backoff.
    """
    try:
        asyncio.run(QBOImportService.process_run(run_id, tenant_id))
    except QBORateLimitExceeded as exc:
        # Retry after rate limit delay, do not mark run as failed in DB for transient throttling.
        raise self.retry(exc=exc)
