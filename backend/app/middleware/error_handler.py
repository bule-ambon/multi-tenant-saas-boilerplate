"""
Error Handler Middleware
Centralized error handling and logging
"""
import logging
import traceback
from typing import Callable

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware for centralized error handling
    Catches exceptions and returns appropriate JSON responses
    """

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request and handle errors"""

        try:
            response = await call_next(request)
            return response

        except SQLAlchemyError as e:
            # Database errors
            logger.error(f"Database error: {e}", exc_info=True)

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "database_error",
                    "detail": "A database error occurred",
                    "message": str(e) if settings.DEBUG else "Database operation failed",
                },
            )

        except ValueError as e:
            # Validation errors
            logger.warning(f"Validation error: {e}")

            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "validation_error",
                    "detail": str(e),
                },
            )

        except PermissionError as e:
            # Permission/authorization errors
            logger.warning(f"Permission error: {e}")

            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "permission_denied",
                    "detail": str(e) or "You don't have permission to perform this action",
                },
            )

        except Exception as e:
            # Unexpected errors
            logger.error(
                f"Unhandled exception: {e}\n{traceback.format_exc()}",
                exc_info=True,
            )

            # Send to Sentry if configured
            if settings.SENTRY_DSN:
                # Sentry integration would go here
                pass

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "internal_server_error",
                    "detail": "An unexpected error occurred",
                    "message": str(e) if settings.DEBUG else None,
                    "traceback": traceback.format_exc() if settings.DEBUG else None,
                },
            )
