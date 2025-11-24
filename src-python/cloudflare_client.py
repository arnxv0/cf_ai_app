"""
cloudflare_client.py — Thin async HTTP client for the Pointer Cloudflare Worker.

Mirrors the Rust client: chat streaming, memory ingestion, memory search.
Reads config from the settings_manager (cloudflare category).
"""
from __future__ import annotations

import logging
from typing import AsyncIterator, Any, Optional

import httpx

from utils.settings_manager import get_settings_manager

logger = logging.getLogger("pointer.cloudflare")


def _get_config() -> dict[str, Any]:
    """Read cloudflare settings from the settings DB."""
    sm = get_settings_manager()
    return {
        "enabled": sm.get("cloudflare", "enabled", default=False),
        "endpoint": sm.get("cloudflare", "endpoint", default=""),
        "api_token": sm.get("cloudflare", "api_token", default="", decrypt=True),
        "default_model": sm.get("cloudflare", "default_model", default="@cf/meta/llama-3.3-70b-instruct-fp8-fast"),
        "rag_top_k": sm.get("cloudflare", "rag_top_k", default=5),
    }


def is_enabled() -> bool:
    """Return True if Cloudflare integration is configured and enabled."""
    cfg = _get_config()
    return bool(cfg["enabled"] and cfg["endpoint"] and cfg["api_token"])


def _headers() -> dict[str, str]:
    cfg = _get_config()
    return {
        "Authorization": f"Bearer {cfg['api_token']}",
        "Content-Type": "application/json",
    }


def _base_url() -> str:
    return _get_config()["endpoint"].rstrip("/")


# ──────────────────────────────── Chat ───────────────────────────────────────

async def stream_chat(
    messages: list[dict[str, str]],
    system: Optional[str] = None,
) -> AsyncIterator[str]:
    """
    Stream chat tokens from the Cloudflare Worker's /api/chat endpoint.

    Yields decoded token strings as they arrive (SSE text/event-stream).
    """
    url = f"{_base_url()}/api/chat"
    payload: dict[str, Any] = {"messages": messages}
    if system:
        payload["system"] = system

    async with httpx.AsyncClient(timeout=60) as client:
        async with client.stream("POST", url, json=payload, headers=_headers()) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data.strip() == "[DONE]":
                        return
                    yield data


# ──────────────────────────────── Memory ─────────────────────────────────────

async def ingest_memory(
    text: str,
    metadata: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Chunk, embed, and store text in Vectorize via the Worker's ingest endpoint.

    Returns the Worker's JSON response: {"ok": true, "chunks_ingested": N}
    """
    url = f"{_base_url()}/api/memory/ingest"
    payload: dict[str, Any] = {"text": text}
    if metadata:
        payload["metadata"] = metadata

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=payload, headers=_headers())
        resp.raise_for_status()
        return resp.json()


async def search_memory(
    query: str,
    top_k: Optional[int] = None,
) -> list[dict[str, Any]]:
    """
    Search Vectorize for the top-K memories most similar to `query`.

    Returns a list of match dicts: [{"id": ..., "score": ..., "text": ..., "metadata": ...}]
    """
    cfg = _get_config()
    url = f"{_base_url()}/api/memory/search"
    payload: dict[str, Any] = {
        "query": query,
        "top_k": top_k or cfg["rag_top_k"],
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=payload, headers=_headers())
        resp.raise_for_status()
        data = resp.json()
        return data.get("matches", [])


# ──────────────────────────── Context Builder ──────────────────────────────

async def build_cloudflare_context(query: str) -> str:
    """
    Search memory for relevant chunks and format them as a system-prompt prefix.

    Returns empty string if Cloudflare is disabled or search fails.
    """
    if not is_enabled():
        return ""

    try:
        matches = await search_memory(query)
        if not matches:
            return ""

        chunks = [m["text"] for m in matches if m.get("text")]
        context = "\n---\n".join(chunks)
        return (
            "Relevant context from memory:\n"
            f"{context}\n"
            "---\n"
            "Use the above context to inform your response if relevant.\n"
        )
    except Exception as exc:
        logger.warning("Cloudflare memory search failed (fallback to local): %s", exc)
        return ""
