"""
Structured Logging Configuration - ITEM 34

Features:
- JSON output for log aggregation
- Correlation IDs for request tracing
- Log rotation (10MB files, 5 backups)
- Log levels from environment
- Contextual logging (user, request, etc.)
"""

import os
import sys
import logging
import logging.handlers
import json
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import uuid4
from contextvars import ContextVar

# ============================================================================
# Context Variables for Request Tracking
# ============================================================================
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
request_path_var: ContextVar[Optional[str]] = ContextVar('request_path', default=None)


# ============================================================================
# JSON Formatter
# ============================================================================
class JSONFormatter(logging.Formatter):
    """
    Format log records as JSON for structured logging.

    Includes correlation ID, user context, and request information.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add correlation ID if available
        correlation_id = correlation_id_var.get()
        if correlation_id:
            log_data["correlation_id"] = correlation_id

        # Add user ID if available
        user_id = user_id_var.get()
        if user_id:
            log_data["user_id"] = user_id

        # Add request path if available
        request_path = request_path_var.get()
        if request_path:
            log_data["request_path"] = request_path

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        # Add extra fields from record
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        return json.dumps(log_data, default=str)


# ============================================================================
# Correlation ID Middleware
# ============================================================================
def generate_correlation_id() -> str:
    """
    Generate a unique correlation ID for request tracing.

    Returns:
        UUID string
    """
    return str(uuid4())


def set_correlation_id(correlation_id: str):
    """
    Set correlation ID for current context.

    Args:
        correlation_id: Correlation ID to set
    """
    correlation_id_var.set(correlation_id)


def get_correlation_id() -> Optional[str]:
    """
    Get correlation ID from current context.

    Returns:
        Correlation ID or None
    """
    return correlation_id_var.get()


def set_user_context(user_id: str):
    """
    Set user ID for current context.

    Args:
        user_id: User ID to set
    """
    user_id_var.set(user_id)


def set_request_context(request_path: str):
    """
    Set request path for current context.

    Args:
        request_path: Request path to set
    """
    request_path_var.set(request_path)


# ============================================================================
# Logging Configuration
# ============================================================================
def configure_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = True,
) -> None:
    """
    Configure application logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path (with rotation)
        json_format: Use JSON formatting (True) or plain text (False)
    """
    # Get log level from environment or parameter
    level_name = os.getenv("LOG_LEVEL", log_level).upper()
    level = getattr(logging, level_name, logging.INFO)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Choose formatter
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation (if log_file specified)
    if log_file:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        # Rotating file handler: 10MB per file, keep 5 backups
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8',
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Configure third-party loggers
    # Reduce noise from verbose libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)

    # Log configuration completion
    root_logger.info(
        f"Logging configured: level={level_name}, json={json_format}, file={log_file or 'None'}"
    )


# ============================================================================
# Contextual Logger
# ============================================================================
class ContextLogger:
    """
    Logger that automatically includes context variables.

    Usage:
        logger = ContextLogger(__name__)
        logger.info("User logged in")  # Includes correlation ID, user ID
    """

    def __init__(self, name: str):
        """
        Initialize context logger.

        Args:
            name: Logger name
        """
        self.logger = logging.getLogger(name)

    def _add_context(self, extra: Optional[Dict] = None) -> Dict:
        """Add context variables to extra dict."""
        context = extra or {}

        correlation_id = get_correlation_id()
        if correlation_id:
            context["correlation_id"] = correlation_id

        user_id = user_id_var.get()
        if user_id:
            context["user_id"] = user_id

        request_path = request_path_var.get()
        if request_path:
            context["request_path"] = request_path

        return context

    def debug(self, message: str, extra: Optional[Dict] = None):
        """Log debug message with context."""
        self.logger.debug(message, extra=self._add_context(extra))

    def info(self, message: str, extra: Optional[Dict] = None):
        """Log info message with context."""
        self.logger.info(message, extra=self._add_context(extra))

    def warning(self, message: str, extra: Optional[Dict] = None):
        """Log warning message with context."""
        self.logger.warning(message, extra=self._add_context(extra))

    def error(self, message: str, extra: Optional[Dict] = None, exc_info=False):
        """Log error message with context."""
        self.logger.error(message, extra=self._add_context(extra), exc_info=exc_info)

    def critical(self, message: str, extra: Optional[Dict] = None, exc_info=False):
        """Log critical message with context."""
        self.logger.critical(message, extra=self._add_context(extra), exc_info=exc_info)

    def exception(self, message: str, extra: Optional[Dict] = None):
        """Log exception with traceback and context."""
        self.logger.exception(message, extra=self._add_context(extra))


# ============================================================================
# Request Logging Middleware (FastAPI)
# ============================================================================
async def logging_middleware(request, call_next):
    """
    FastAPI middleware for request logging with correlation IDs.

    Automatically generates correlation ID and logs requests.

    Usage in FastAPI:
        app.middleware("http")(logging_middleware)
    """
    from fastapi import Request

    # Generate or extract correlation ID
    correlation_id = request.headers.get("X-Correlation-ID")
    if not correlation_id:
        correlation_id = generate_correlation_id()

    # Set context variables
    set_correlation_id(correlation_id)
    set_request_context(request.url.path)

    # Log request
    logger = ContextLogger(__name__)
    logger.info(
        f"{request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client_host": request.client.host if request.client else None,
        }
    )

    # Process request
    import time
    start_time = time.time()

    try:
        response = await call_next(request)
        elapsed = time.time() - start_time

        # Log response
        logger.info(
            f"Response {response.status_code}",
            extra={
                "status_code": response.status_code,
                "response_time_ms": round(elapsed * 1000, 2),
            }
        )

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        return response

    except Exception as e:
        elapsed = time.time() - start_time
        logger.exception(
            f"Request failed: {str(e)}",
            extra={
                "response_time_ms": round(elapsed * 1000, 2),
            }
        )
        raise


# ============================================================================
# Initialize Logging
# ============================================================================
def setup_application_logging():
    """
    Setup application logging on startup.

    Call this in main.py or app initialization.
    """
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.getenv("LOG_FILE", "/var/log/cerebrum/app.log")
    json_format = os.getenv("LOG_JSON", "true").lower() == "true"

    # Don't use file logging in development (stdout only)
    environment = os.getenv("ENVIRONMENT", "development")
    if environment == "development":
        log_file = None

    configure_logging(
        log_level=log_level,
        log_file=log_file,
        json_format=json_format,
    )


# ============================================================================
# Exports
# ============================================================================
__all__ = [
    "configure_logging",
    "ContextLogger",
    "set_correlation_id",
    "get_correlation_id",
    "generate_correlation_id",
    "set_user_context",
    "set_request_context",
    "logging_middleware",
    "setup_application_logging",
]
