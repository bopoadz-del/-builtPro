"""Compatibility entrypoint for tests expecting backend.main."""

from __future__ import annotations

import importlib
import os

os.environ.setdefault("ENV", "development")

import main as main_module

app = importlib.reload(main_module).app

__all__ = ["app"]
