"""
Base helper module for all Lumi Virtual Lab MCP servers.

Provides:
- async_http_get / async_http_post with retry + timeout
- standard_response / handle_error for consistent output format
- Per-domain async semaphore rate limiting
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx

logger = logging.getLogger("lumi.mcp.base")

# ---------------------------------------------------------------------------
# Rate-limiting: one semaphore per domain, configurable concurrency
# ---------------------------------------------------------------------------

_domain_semaphores: dict[str, asyncio.Semaphore] = {}
_DEFAULT_CONCURRENCY = 5  # max concurrent requests per domain


def _get_semaphore(url: str, max_concurrent: int = _DEFAULT_CONCURRENCY) -> asyncio.Semaphore:
    """Return (or create) an asyncio.Semaphore for the domain in *url*."""
    domain = urlparse(url).netloc
    if domain not in _domain_semaphores:
        _domain_semaphores[domain] = asyncio.Semaphore(max_concurrent)
    return _domain_semaphores[domain]


# ---------------------------------------------------------------------------
# Retry / timeout constants
# ---------------------------------------------------------------------------

MAX_RETRIES = 3
BASE_BACKOFF = 1.0        # seconds; doubles each retry
DEFAULT_TIMEOUT = 30.0    # seconds


# ---------------------------------------------------------------------------
# Core HTTP helpers
# ---------------------------------------------------------------------------

async def async_http_get(
    url: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = MAX_RETRIES,
) -> dict[str, Any]:
    """
    Perform an async HTTP GET with retry (exponential back-off) and timeout.

    Returns the parsed JSON body on success, or raises after exhausting retries.
    """
    sem = _get_semaphore(url)
    last_exc: Exception | None = None

    for attempt in range(1, max_retries + 1):
        async with sem:
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.get(url, params=params, headers=headers)
                    resp.raise_for_status()
                    # Some APIs return plain text or XML; try JSON first
                    try:
                        return resp.json()
                    except (json.JSONDecodeError, ValueError):
                        return {"text": resp.text}
            except (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException) as exc:
                last_exc = exc
                if attempt < max_retries:
                    wait = BASE_BACKOFF * (2 ** (attempt - 1))
                    logger.warning(
                        "GET %s attempt %d/%d failed (%s). Retrying in %.1fs ...",
                        url, attempt, max_retries, exc, wait,
                    )
                    await asyncio.sleep(wait)

    raise last_exc  # type: ignore[misc]


async def async_http_post(
    url: str,
    data: dict[str, Any] | str | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = MAX_RETRIES,
) -> dict[str, Any]:
    """
    Perform an async HTTP POST with retry (exponential back-off) and timeout.

    If *data* is a dict it is sent as JSON; if it is a string it is sent as
    the raw body (useful for GraphQL query strings already serialised).
    """
    sem = _get_semaphore(url)
    last_exc: Exception | None = None

    for attempt in range(1, max_retries + 1):
        async with sem:
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    if isinstance(data, dict):
                        resp = await client.post(url, json=data, headers=headers)
                    else:
                        resp = await client.post(url, content=data, headers=headers)
                    resp.raise_for_status()
                    try:
                        return resp.json()
                    except (json.JSONDecodeError, ValueError):
                        return {"text": resp.text}
            except (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException) as exc:
                last_exc = exc
                if attempt < max_retries:
                    wait = BASE_BACKOFF * (2 ** (attempt - 1))
                    logger.warning(
                        "POST %s attempt %d/%d failed (%s). Retrying in %.1fs ...",
                        url, attempt, max_retries, exc, wait,
                    )
                    await asyncio.sleep(wait)

    raise last_exc  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Standard response builders
# ---------------------------------------------------------------------------

def standard_response(
    summary: str,
    raw_data: dict[str, Any],
    source: str,
    source_id: str,
    version: str | None = None,
    confidence: float = 0.8,
) -> dict[str, Any]:
    """
    Build the canonical Lumi response envelope.

    Every tool across every MCP server should return this shape so that
    upstream agents can rely on a consistent schema.
    """
    return {
        "summary": summary,
        "raw_data": raw_data,
        "provenance": {
            "source": source,
            "source_id": source_id,
            "version": version or "latest",
            "access_date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "confidence": confidence,
    }


def handle_error(tool_name: str, error: Exception | str) -> dict[str, Any]:
    """
    Return a structured error response that agents can inspect without crashing.
    """
    error_msg = str(error)
    logger.error("Tool %s error: %s", tool_name, error_msg)
    return {
        "error": True,
        "tool": tool_name,
        "message": error_msg,
        "provenance": {
            "source": tool_name,
            "source_id": "error",
            "version": None,
            "access_date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "confidence": 0.0,
    }
