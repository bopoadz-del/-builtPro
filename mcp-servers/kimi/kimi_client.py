"""Async Kimi/Moonshot API client for MCP server integration."""

from __future__ import annotations

import os
from typing import Any

import httpx


class KimiConfigurationError(ValueError):
    """Raised when the Kimi client is misconfigured."""


class KimiAPIError(RuntimeError):
    """Raised when a Kimi API call fails."""


class KimiClient:
    """Async HTTP client for Kimi/Moonshot API."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("MOONSHOT_API_KEY", "").strip()
        if not self.api_key:
            raise KimiConfigurationError(
                "MOONSHOT_API_KEY is not set. "
                "Set it as an environment variable or pass api_key directly."
            )
        self.base_url = (
            base_url or os.getenv("KIMI_BASE_URL", "https://api.moonshot.ai/v1")
        ).rstrip("/")

    async def complete(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str = "kimi-k2.5",
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        """Send a chat completion request and return the assistant's reply."""
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise KimiAPIError(
                    f"Kimi API returned {exc.response.status_code}: "
                    f"{exc.response.text}"
                ) from exc
            except httpx.HTTPError as exc:
                raise KimiAPIError(f"Kimi API request failed: {exc}") from exc

        data = response.json()
        return data["choices"][0]["message"]["content"]
