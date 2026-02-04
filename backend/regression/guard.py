"""Regression guard stub."""

from __future__ import annotations


class RegressionGuard:
    def __init__(self) -> None:
        self.enabled = True

    def check(self) -> bool:
        return self.enabled
