"""Slack MCP Server — post messages, reply in threads, read channels.

Requires ``LUMI_SLACK_BOT_TOKEN`` env var.  Slack App needs scopes:
``chat:write``, ``channels:read``, ``channels:history``.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

try:
    from fastmcp import FastMCP
except ImportError:
    from mcp.server.fastmcp import FastMCP

try:
    from src.mcp_servers.base import async_http_post, async_http_get, handle_error, standard_response
except ImportError:
    from mcp_servers.base import async_http_post, async_http_get, handle_error, standard_response

logger = logging.getLogger("lumi.mcp.slack")

mcp = FastMCP(
    "Lumi Slack",
    instructions="Post messages, reply in threads, and read channels in a Slack workspace.",
)

SLACK_API = "https://slack.com/api"


def _headers() -> dict[str, str]:
    token = os.environ.get("LUMI_SLACK_BOT_TOKEN", "")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8",
    }


def _check_token() -> str:
    token = os.environ.get("LUMI_SLACK_BOT_TOKEN", "")
    if not token:
        raise RuntimeError("LUMI_SLACK_BOT_TOKEN not set")
    return token


@mcp.tool()
async def slack_post_message(
    channel: str,
    text: str,
    blocks_json: str | None = None,
    username: str | None = None,
    icon_emoji: str | None = None,
) -> dict[str, Any]:
    """Post a message to a Slack channel.  Returns the message timestamp (ts)."""
    try:
        _check_token()
        payload: dict[str, Any] = {"channel": channel, "text": text}
        if blocks_json:
            try:
                payload["blocks"] = json.loads(blocks_json) if isinstance(blocks_json, str) else blocks_json
            except json.JSONDecodeError as exc:
                return handle_error("slack_post_message", f"Invalid blocks_json: {exc}")
        if username:
            payload["username"] = username
        if icon_emoji:
            payload["icon_emoji"] = icon_emoji

        data = await async_http_post(
            f"{SLACK_API}/chat.postMessage",
            data=payload,
            headers=_headers(),
            max_retries=2,
        )

        if not data.get("ok"):
            return handle_error("slack_post_message", f"Slack API error: {data.get('error', 'unknown')}")

        return standard_response(
            summary=f"Message posted to {channel} (ts: {data.get('ts', '')})",
            raw_data={"ts": data.get("ts"), "channel": data.get("channel")},
            source="Slack",
            source_id=data.get("ts", ""),
            confidence=1.0,
        )
    except Exception as exc:
        return handle_error("slack_post_message", exc)


@mcp.tool()
async def slack_post_thread_reply(
    channel: str,
    thread_ts: str,
    text: str,
    username: str | None = None,
    icon_emoji: str | None = None,
) -> dict[str, Any]:
    """Reply to a message thread in Slack."""
    try:
        _check_token()
        payload: dict[str, Any] = {
            "channel": channel,
            "thread_ts": thread_ts,
            "text": text,
        }
        if username:
            payload["username"] = username
        if icon_emoji:
            payload["icon_emoji"] = icon_emoji

        data = await async_http_post(
            f"{SLACK_API}/chat.postMessage",
            data=payload,
            headers=_headers(),
            max_retries=2,
        )

        if not data.get("ok"):
            return handle_error("slack_post_thread_reply", f"Slack API error: {data.get('error', 'unknown')}")

        return standard_response(
            summary=f"Thread reply posted (ts: {data.get('ts', '')})",
            raw_data={"ts": data.get("ts"), "channel": data.get("channel"), "thread_ts": thread_ts},
            source="Slack",
            source_id=data.get("ts", ""),
            confidence=1.0,
        )
    except Exception as exc:
        return handle_error("slack_post_thread_reply", exc)


@mcp.tool()
async def slack_list_channels(limit: int = 100) -> dict[str, Any]:
    """List public channels in the Slack workspace."""
    try:
        _check_token()
        data = await async_http_get(
            f"{SLACK_API}/conversations.list",
            params={"types": "public_channel", "limit": str(limit)},
            headers=_headers(),
            max_retries=2,
        )

        if not data.get("ok"):
            return handle_error("slack_list_channels", f"Slack API error: {data.get('error', 'unknown')}")

        channels = [
            {"id": ch["id"], "name": ch["name"], "topic": ch.get("topic", {}).get("value", "")}
            for ch in data.get("channels", [])
        ]
        return standard_response(
            summary=f"Found {len(channels)} channels",
            raw_data={"channels": channels},
            source="Slack",
            source_id="conversations.list",
            confidence=1.0,
        )
    except Exception as exc:
        return handle_error("slack_list_channels", exc)


@mcp.tool()
async def slack_get_thread_replies(
    channel: str,
    thread_ts: str,
    limit: int = 20,
) -> dict[str, Any]:
    """Get replies in a Slack message thread."""
    try:
        _check_token()
        data = await async_http_get(
            f"{SLACK_API}/conversations.replies",
            params={"channel": channel, "ts": thread_ts, "limit": str(limit)},
            headers=_headers(),
            max_retries=2,
        )

        if not data.get("ok"):
            return handle_error("slack_get_thread_replies", f"Slack API error: {data.get('error', 'unknown')}")

        messages = [
            {"ts": m.get("ts"), "user": m.get("user", ""), "text": m.get("text", "")}
            for m in data.get("messages", [])
        ]
        return standard_response(
            summary=f"Thread has {len(messages)} messages",
            raw_data={"messages": messages, "thread_ts": thread_ts},
            source="Slack",
            source_id=thread_ts,
            confidence=1.0,
        )
    except Exception as exc:
        return handle_error("slack_get_thread_replies", exc)


if __name__ == "__main__":
    mcp.run()
