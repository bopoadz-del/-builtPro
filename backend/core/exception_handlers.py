"""
Global Exception Handlers - ITEM 39

Standardized error responses for all exception types:
- HTTPException (FastAPI)
- ValidationError (Pydantic)
- SQLAlchemyError (Database)
- Custom application exceptions

All errors return consistent JSON structure with correlation IDs.
"""

import traceback
from typing import Union
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.core.logging_config import ContextLogger, get_correlation_id

logger = ContextLogger(__name__)


# ============================================================================
# Standard Error Response Format
# ============================================================================
def create_error_response(
    request: Request,
    status_code: int,
    error_type: str,
    message: str,
    details: Union[dict, list, None] = None,
) -> JSONResponse:
    """
    Create standardized error response.

    Args:
        request: FastAPI request
        status_code: HTTP status code
        error_type: Error type (e.g., "ValidationError", "DatabaseError")
        message: Human-readable error message
        details: Optional detailed error information

    Returns:
        JSON response with standard error format
    """
    error_data = {
        "error": {
            "type": error_type,
            "message": message,
            "path": request.url.path,
            "method": request.method,
            "correlation_id": get_correlation_id(),
        }
    }

    if details:
        error_data["error"]["details"] = details

    # Add timestamp
    from datetime import datetime
    error_data["error"]["timestamp"] = datetime.utcnow().isoformat() + "Z"

    return JSONResponse(
        status_code=status_code,
        content=error_data,
    )


# ============================================================================
# Exception Handlers
# ============================================================================

async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
) -> JSONResponse:
    """
    Handle FastAPI HTTPException.

    Args:
        request: FastAPI request
        exc: HTTP exception

    Returns:
        Standardized error response
    """
    logger.warning(
        f"HTTP {exc.status_code}: {exc.detail}",
        extra={"status_code": exc.status_code}
    )

    return create_error_response(
        request=request,
        status_code=exc.status_code,
        error_type="HTTPException",
        message=str(exc.detail),
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors.

    Formats validation errors in a user-friendly way.

    Args:
        request: FastAPI request
        exc: Validation error

    Returns:
        Standardized error response with validation details
    """
    # Format validation errors
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })

    logger.warning(
        f"Validation error: {len(errors)} fields failed",
        extra={"error_count": len(errors)}
    )

    return create_error_response(
        request=request,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_type="ValidationError",
        message="Request validation failed",
        details=errors,
    )


async def sqlalchemy_exception_handler(
    request: Request,
    exc: SQLAlchemyError
) -> JSONResponse:
    """
    Handle SQLAlchemy database errors.

    Args:
        request: FastAPI request
        exc: SQLAlchemy exception

    Returns:
        Standardized error response
    """
    # Determine error type and message
    if isinstance(exc, IntegrityError):
        error_type = "DatabaseIntegrityError"
        message = "Database integrity constraint violated"
        status_code = status.HTTP_409_CONFLICT

        # Try to extract constraint name
        constraint = str(exc.orig) if hasattr(exc, 'orig') else str(exc)
        if "duplicate key" in constraint.lower():
            message = "Duplicate entry - record already exists"
        elif "foreign key" in constraint.lower():
            message = "Referenced record does not exist"

    elif isinstance(exc, OperationalError):
        error_type = "DatabaseOperationalError"
        message = "Database operation failed"
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    else:
        error_type = "DatabaseError"
        message = "Database error occurred"
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    # Log the full error (don't expose to user)
    logger.error(
        f"Database error: {type(exc).__name__}",
        extra={"exception": str(exc)},
        exc_info=True
    )

    # Return sanitized error
    return create_error_response(
        request=request,
        status_code=status_code,
        error_type=error_type,
        message=message,
    )


async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handle all other unhandled exceptions.

    This is the catch-all handler for unexpected errors.

    Args:
        request: FastAPI request
        exc: Any exception

    Returns:
        Standardized error response
    """
    # Log full exception with traceback
    logger.exception(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        extra={
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
        }
    )

    # Return generic error (don't expose internal details)
    return create_error_response(
        request=request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_type="InternalServerError",
        message="An unexpected error occurred. Please try again later.",
    )


# ============================================================================
# Custom Application Exceptions
# ============================================================================

class CerebrumException(Exception):
    """Base exception for Cerebrum application."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Union[dict, list, None] = None,
    ):
        """
        Initialize Cerebrum exception.

        Args:
            message: Error message
            status_code: HTTP status code
            details: Optional error details
        """
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class ResourceNotFoundError(CerebrumException):
    """Resource not found exception."""

    def __init__(self, resource_type: str, resource_id: str):
        """
        Initialize resource not found error.

        Args:
            resource_type: Type of resource (e.g., "Project", "User")
            resource_id: ID of resource
        """
        super().__init__(
            message=f"{resource_type} with ID '{resource_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource_type": resource_type, "resource_id": resource_id},
        )


class PermissionDeniedError(CerebrumException):
    """Permission denied exception."""

    def __init__(self, action: str, resource: str):
        """
        Initialize permission denied error.

        Args:
            action: Action being attempted
            resource: Resource being accessed
        """
        super().__init__(
            message=f"Permission denied to {action} {resource}",
            status_code=status.HTTP_403_FORBIDDEN,
            details={"action": action, "resource": resource},
        )


class BusinessLogicError(CerebrumException):
    """Business logic validation error."""

    def __init__(self, message: str, details: Union[dict, list, None] = None):
        """
        Initialize business logic error.

        Args:
            message: Error message
            details: Optional error details
        """
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class ServiceUnavailableError(CerebrumException):
    """Service unavailable exception."""

    def __init__(self, service_name: str, message: str = None):
        """
        Initialize service unavailable error.

        Args:
            service_name: Name of unavailable service
            message: Optional custom message
        """
        default_message = f"{service_name} is currently unavailable"
        super().__init__(
            message=message or default_message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"service": service_name},
        )


async def cerebrum_exception_handler(
    request: Request,
    exc: CerebrumException
) -> JSONResponse:
    """
    Handle custom Cerebrum exceptions.

    Args:
        request: FastAPI request
        exc: Cerebrum exception

    Returns:
        Standardized error response
    """
    logger.warning(
        f"Cerebrum exception: {exc.message}",
        extra={"status_code": exc.status_code}
    )

    return create_error_response(
        request=request,
        status_code=exc.status_code,
        error_type=type(exc).__name__,
        message=exc.message,
        details=exc.details,
    )


# ============================================================================
# Register Exception Handlers
# ============================================================================
def register_exception_handlers(app):
    """
    Register all exception handlers with FastAPI app.

    Args:
        app: FastAPI application instance

    Usage:
        from fastapi import FastAPI
        app = FastAPI()
        register_exception_handlers(app)
    """
    # FastAPI built-in exceptions
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    # Database exceptions
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)

    # Custom Cerebrum exceptions
    app.add_exception_handler(CerebrumException, cerebrum_exception_handler)

    # Catch-all for unhandled exceptions
    app.add_exception_handler(Exception, general_exception_handler)

    logger.info("Exception handlers registered")


# ============================================================================
# Exports
# ============================================================================
__all__ = [
    "register_exception_handlers",
    "CerebrumException",
    "ResourceNotFoundError",
    "PermissionDeniedError",
    "BusinessLogicError",
    "ServiceUnavailableError",
]
