"""Backend shim for database logging utilities."""

from __future__ import annotations

import importlib

_db_module = importlib.import_module("db")

log_alert = _db_module.log_alert
log_approval = _db_module.log_approval
