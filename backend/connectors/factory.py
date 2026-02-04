"""Connector factory helpers."""

from __future__ import annotations

import os
from typing import Dict


def get_connector(connector_type: str) -> Dict[str, str]:
    if os.getenv("USE_STUB_CONNECTORS", "false").lower() == "true":
        mapping = {
            "aconex": {"status": "stubbed"},
            "p6": {"status": "stubbed"},
            "vision": {"status": "stubbed"},
        }
        return mapping.get(connector_type, {"status": "stubbed"})
    return {"status": "unconfigured"}
