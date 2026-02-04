"""Backend shim for validation helpers."""

from __future__ import annotations

import importlib

validation_module = importlib.import_module("validation")

validate_quantities = validation_module.validate_quantities
