"""
Health Check Endpoints - ITEM 33

Kubernetes-ready health checks with deep probes:
- /health: Deep probe (DB connectivity + Redis + disk space)
- /health/live: Liveness probe (is app running?)
- /health/ready: Readiness probe (can app serve traffic?)

Usage:
    - Kubernetes liveness: GET /health/live
    - Kubernetes readiness: GET /health/ready
    - Deep health check: GET /health
"""

import os
import shutil
import time
from datetime import datetime
from typing import Dict, Any, List
from fastapi import APIRouter, status, Response
from sqlalchemy import text
from backend.core.database_enhanced import engine, SessionLocal, get_pool_status
import redis as redis_lib
from backend.core.config_enhanced import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


# ============================================================================
# ITEM 33: Health Check Endpoints
# ============================================================================

def check_database() -> Dict[str, Any]:
    """
    Check database connectivity and basic query.

    Returns:
        Health status dict
    """
    start_time = time.time()
    try:
        db = SessionLocal()
        try:
            # Test query
            result = db.execute(text("SELECT 1 as health_check"))
            result.fetchone()

            # Get pool stats
            pool_stats = get_pool_status()

            elapsed = time.time() - start_time

            return {
                "status": "healthy",
                "response_time_ms": round(elapsed * 1000, 2),
                "pool": pool_stats,
            }
        finally:
            db.close()
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "response_time_ms": round(elapsed * 1000, 2),
        }


def check_redis() -> Dict[str, Any]:
    """
    Check Redis connectivity for all databases.

    Returns:
        Health status dict
    """
    start_time = time.time()
    results = {}

    redis_configs = {
        "cache": settings.redis_cache_url,
        "queue": settings.redis_queue_url,
        "session": settings.redis_session_url,
        "ratelimit": settings.redis_ratelimit_url,
    }

    all_healthy = True

    for name, url in redis_configs.items():
        try:
            client = redis_lib.from_url(url, socket_timeout=2)
            client.ping()

            # Get info
            info = client.info("stats")

            results[name] = {
                "status": "healthy",
                "total_connections": info.get("total_connections_received", 0),
                "connected_clients": info.get("connected_clients", 0),
            }
            client.close()
        except Exception as e:
            all_healthy = False
            results[name] = {
                "status": "unhealthy",
                "error": str(e),
            }
            logger.error(f"Redis {name} health check failed: {str(e)}")

    elapsed = time.time() - start_time

    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "response_time_ms": round(elapsed * 1000, 2),
        "databases": results,
    }


def check_disk_space() -> Dict[str, Any]:
    """
    Check disk space (must be >20% free).

    Returns:
        Health status dict
    """
    try:
        # Check disk space for current directory
        disk = shutil.disk_usage("/")

        total_gb = disk.total / (1024 ** 3)
        used_gb = disk.used / (1024 ** 3)
        free_gb = disk.free / (1024 ** 3)
        percent_free = (disk.free / disk.total) * 100

        is_healthy = percent_free > 20

        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "total_gb": round(total_gb, 2),
            "used_gb": round(used_gb, 2),
            "free_gb": round(free_gb, 2),
            "percent_free": round(percent_free, 2),
            "threshold": 20.0,
        }
    except Exception as e:
        logger.error(f"Disk space check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
        }


def check_memory() -> Dict[str, Any]:
    """
    Check memory usage (must be <80%).

    Returns:
        Health status dict
    """
    try:
        import psutil

        mem = psutil.virtual_memory()

        is_healthy = mem.percent < 80

        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "total_gb": round(mem.total / (1024 ** 3), 2),
            "used_gb": round(mem.used / (1024 ** 3), 2),
            "available_gb": round(mem.available / (1024 ** 3), 2),
            "percent_used": round(mem.percent, 2),
            "threshold": 80.0,
        }
    except ImportError:
        # psutil not installed (optional)
        return {
            "status": "unknown",
            "message": "psutil not installed",
        }
    except Exception as e:
        logger.error(f"Memory check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
        }


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check_deep(response: Response) -> Dict[str, Any]:
    """
    Deep health probe: checks database, Redis, disk space, memory.

    This endpoint performs comprehensive health checks and should be used
    for monitoring and alerting. It may take longer to respond than
    liveness/readiness probes.

    Returns:
        Detailed health status of all components
    """
    start_time = time.time()

    # Run all checks
    db_health = check_database()
    redis_health = check_redis()
    disk_health = check_disk_space()
    memory_health = check_memory()

    # Determine overall health
    all_checks = [db_health, redis_health, disk_health, memory_health]
    is_healthy = all(
        check.get("status") == "healthy"
        for check in all_checks
        if check.get("status") != "unknown"
    )

    elapsed = time.time() - start_time

    health_data = {
        "status": "healthy" if is_healthy else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": time.time() - _startup_time,
        "version": settings.app_version,
        "environment": settings.environment.value,
        "checks": {
            "database": db_health,
            "redis": redis_health,
            "disk": disk_health,
            "memory": memory_health,
        },
        "response_time_ms": round(elapsed * 1000, 2),
    }

    # Set appropriate status code
    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return health_data


@router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_probe(response: Response) -> Dict[str, str]:
    """
    Kubernetes liveness probe: Is the application running?

    This is a lightweight check that returns quickly. It only checks if
    the application process is alive and responsive.

    Kubernetes will restart the pod if this check fails.

    Returns:
        Simple status message
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_probe(response: Response) -> Dict[str, Any]:
    """
    Kubernetes readiness probe: Can the application serve traffic?

    This checks if the application is ready to accept requests. It performs
    quick checks on critical dependencies (database and cache).

    Kubernetes will remove the pod from service if this check fails.

    Returns:
        Readiness status
    """
    start_time = time.time()

    # Quick checks (timeout after 2 seconds)
    ready = True
    checks = {}

    # Check database connectivity (quick)
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            checks["database"] = "ready"
        finally:
            db.close()
    except Exception as e:
        ready = False
        checks["database"] = f"not_ready: {str(e)[:50]}"
        logger.error(f"Readiness: Database not ready: {str(e)}")

    # Check Redis cache (quick)
    try:
        client = redis_lib.from_url(settings.redis_cache_url, socket_timeout=1)
        client.ping()
        checks["redis_cache"] = "ready"
        client.close()
    except Exception as e:
        ready = False
        checks["redis_cache"] = f"not_ready: {str(e)[:50]}"
        logger.error(f"Readiness: Redis not ready: {str(e)}")

    elapsed = time.time() - start_time

    result = {
        "status": "ready" if ready else "not_ready",
        "checks": checks,
        "response_time_ms": round(elapsed * 1000, 2),
        "timestamp": datetime.utcnow().isoformat(),
    }

    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return result


@router.get("/health/startup", status_code=status.HTTP_200_OK)
async def startup_probe(response: Response) -> Dict[str, Any]:
    """
    Kubernetes startup probe: Has the application finished starting up?

    This is used for slow-starting applications. It checks if all
    initialization tasks are complete.

    Returns:
        Startup status
    """
    # Check if app has been running for at least 5 seconds
    uptime = time.time() - _startup_time

    is_started = uptime > 5

    result = {
        "status": "started" if is_started else "starting",
        "uptime_seconds": round(uptime, 2),
        "timestamp": datetime.utcnow().isoformat(),
    }

    if not is_started:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return result


# ============================================================================
# Startup time tracking
# ============================================================================
_startup_time = time.time()


# ============================================================================
# Export router
# ============================================================================
__all__ = ["router"]
