"""PDP middleware for request enforcement."""

from __future__ import annotations

from typing import Callable, Iterable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .policy_engine import PolicyEngine
from .schemas import PolicyDecision, PolicyRequest
from sqlalchemy.exc import OperationalError

from ..db import SessionLocal, get_db
from ..models import User

PUBLIC_ENDPOINTS: Iterable[str] = ("/health", "/healthz")


class PDPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        path = request.url.path
        if self._is_public(path):
            return await call_next(request)

        user_id = self._extract_user_id(request)
        resource_type = self._extract_resource_type(path)
        context = {
            "endpoint": resource_type,
            "ip_address": request.client.host if request.client else None,
        }
        override = request.app.dependency_overrides.get(get_db)
        generator = None
        if override is None:
            db = SessionLocal()
        else:
            generator = override()
            db = next(generator)

        try:
            try:
                if db.query(User).count() == 0:
                    request.state.pdp_decision = PolicyDecision(allowed=True, reason="PDP bypassed")
                    request.state.user_id = user_id
                    return await call_next(request)
            except OperationalError:
                request.state.pdp_decision = PolicyDecision(allowed=True, reason="PDP unavailable")
                request.state.user_id = user_id
                return await call_next(request)
            engine = PolicyEngine(db)
            policy_request = PolicyRequest(
                user_id=user_id,
                action=request.method.lower(),
                resource_type=resource_type,
                resource_id=None,
                context=context,
            )
            decision = engine.evaluate(policy_request)
        finally:
            if generator is not None:
                generator.close()
            db.close()

        request.state.pdp_decision = decision
        request.state.user_id = user_id

        if not decision.allowed:
            status_code = 403
            if "rate limit" in decision.reason.lower():
                status_code = 429
            return JSONResponse(status_code=status_code, content={"detail": decision.reason})

        return await call_next(request)

    @staticmethod
    def _extract_user_id(request: Request) -> int:
        raw = request.headers.get("X-User-ID") or request.headers.get("X-User-Id")
        try:
            return int(raw) if raw is not None else 1
        except ValueError:
            return 1

    @staticmethod
    def _extract_resource_type(path: str) -> str:
        if path.startswith("/api/"):
            segments = path.split("/")
            if len(segments) > 2:
                return segments[2]
        return "root"

    @staticmethod
    def _is_public(path: str) -> bool:
        if path in PUBLIC_ENDPOINTS:
            return True
        if path.startswith("/docs") or path.startswith("/openapi") or path.startswith("/redoc"):
            return True
        return False
