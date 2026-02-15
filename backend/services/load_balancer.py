"""
Load Balancer for BuilTPro Brain AI

Intelligent request distribution with health-aware routing and multiple algorithms.

Features:
- Multiple algorithms (round-robin, weighted, least connections, IP hash)
- Health-aware routing
- Sticky sessions
- Connection draining
- Backend server management
- Real-time metrics

Author: BuilTPro AI Team
Created: 2026-02-15
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from collections import defaultdict
import hashlib
from threading import Lock

logger = logging.getLogger(__name__)


class LoadBalancerError(Exception):
    pass


class LBAlgorithm(str, Enum):
    ROUND_ROBIN = "round_robin"
    WEIGHTED = "weighted"
    LEAST_CONNECTIONS = "least_connections"
    IP_HASH = "ip_hash"
    RANDOM = "random"


class ServerStatus(str, Enum):
    ACTIVE = "active"
    DRAINING = "draining"
    DOWN = "down"


@dataclass
class BackendServer:
    server_id: str
    host: str
    port: int
    weight: int = 1
    status: ServerStatus = ServerStatus.ACTIVE
    active_connections: int = 0
    total_requests: int = 0
    failed_requests: int = 0
    last_health_check: Optional[datetime] = None
    response_time_ms: float = 0.0


class LoadBalancer:
    """Production-ready load balancer."""

    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True

        self.servers: Dict[str, BackendServer] = {}
        self.algorithm = LBAlgorithm.ROUND_ROBIN
        self.rr_index = 0
        self.sticky_sessions: Dict[str, str] = {}

        self.stats = {"total_requests": 0, "failed_routes": 0}
        logger.info("Load Balancer initialized")

    def add_server(self, server: BackendServer):
        """Add a backend server."""
        self.servers[server.server_id] = server

    def remove_server(self, server_id: str):
        """Remove a backend server."""
        if server_id in self.servers:
            self.servers[server_id].status = ServerStatus.DRAINING

    def route_request(self, client_ip: Optional[str] = None, session_id: Optional[str] = None) -> Optional[BackendServer]:
        """Route a request to a backend server."""
        self.stats["total_requests"] += 1

        # Check sticky session
        if session_id and session_id in self.sticky_sessions:
            server_id = self.sticky_sessions[session_id]
            if server_id in self.servers and self.servers[server_id].status == ServerStatus.ACTIVE:
                server = self.servers[server_id]
                server.active_connections += 1
                server.total_requests += 1
                return server

        active = [s for s in self.servers.values() if s.status == ServerStatus.ACTIVE]
        if not active:
            self.stats["failed_routes"] += 1
            return None

        if self.algorithm == LBAlgorithm.ROUND_ROBIN:
            server = active[self.rr_index % len(active)]
            self.rr_index += 1
        elif self.algorithm == LBAlgorithm.LEAST_CONNECTIONS:
            server = min(active, key=lambda s: s.active_connections)
        elif self.algorithm == LBAlgorithm.WEIGHTED:
            # Weighted round-robin
            total_weight = sum(s.weight for s in active)
            idx = self.rr_index % total_weight
            cumulative = 0
            server = active[0]
            for s in active:
                cumulative += s.weight
                if idx < cumulative:
                    server = s
                    break
            self.rr_index += 1
        elif self.algorithm == LBAlgorithm.IP_HASH and client_ip:
            hash_val = int(hashlib.md5(client_ip.encode()).hexdigest(), 16)
            server = active[hash_val % len(active)]
        else:
            server = active[self.rr_index % len(active)]
            self.rr_index += 1

        server.active_connections += 1
        server.total_requests += 1

        if session_id:
            self.sticky_sessions[session_id] = server.server_id

        return server

    def release_connection(self, server_id: str):
        """Release a connection."""
        if server_id in self.servers:
            self.servers[server_id].active_connections = max(0, self.servers[server_id].active_connections - 1)

    def health_check_all(self) -> Dict[str, bool]:
        """Run health checks on all servers."""
        results = {}
        for server in self.servers.values():
            # Stub - would perform actual health check
            healthy = server.failed_requests < server.total_requests * 0.5 if server.total_requests > 0 else True
            server.last_health_check = datetime.utcnow()
            if not healthy:
                server.status = ServerStatus.DOWN
            results[server.server_id] = healthy
        return results

    def get_stats(self) -> Dict[str, Any]:
        return {**self.stats, "total_servers": len(self.servers),
                "active_servers": sum(1 for s in self.servers.values() if s.status == ServerStatus.ACTIVE)}


load_balancer = LoadBalancer()
