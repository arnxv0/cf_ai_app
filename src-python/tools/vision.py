import os
import base64
import mimetypes
import re
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse

from google.adk.tools import FunctionTool

_MAX_INLINE_BYTES = 5 * 1024 * 1024  # 5MB cap for base64 inlining


def _is_url(s: str) -> bool:
    try:
        u = urlparse(s)
        return bool(u.scheme and u.netloc)
    except Exception:
        return False


def _sniff_mime(path_or_url: str) -> str:
    # best-effort guess
    guess, _ = mimetypes.guess_type(path_or_url)
    return guess or "application/octet-stream"


def _inline_image_if_small(path: str) -> Optional[str]:
    """
    If image <= 5MB, return data URL for inline use by the model.
    Otherwise return None (caller will fall back to path).
    """
    try:
        size = os.path.getsize(path)
        if size > _MAX_INLINE_BYTES:
            return None
        mime = _sniff_mime(path)
        if not mime.startswith("image/"):
            return None
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        return f"data:{mime};base64,{b64}"
    except Exception:
        return None


def _normalize_kind(kind: str) -> str:
    k = (kind or "").strip().lower()
    if k in {"img", "picture", "photo"}:
        return "image"
    if k in {"vid", "movie"}:
        return "video"
    if k in {"link", "url"}:
        return "url"
    if k in {"txt", "doc"}:
        return "text"
    return k


def _short(s: str, n: int = 180) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[: n - 1] + "…"


async def attach_context(
    kind: str,
    content: str,
    caption: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Attach optional context for Arrow to use later (returned to the model).
    kind: 'text' | 'image' | 'video' | 'url'
    content:
      - text: the raw text
      - image/video: local filesystem path
      - url: http/https URL
    caption: optional short description from the user
    """
    k = _normalize_kind(kind)
    if k not in {"text", "image", "video", "url"}:
        return {
            "status": "error",
            "error": f"Unsupported kind '{kind}'. Use one of: text, image, video, url.",
        }

    # Build a context payload the LLM can use immediately
    payload: Dict[str, Any] = {"kind": k, "caption": caption or ""}

    if k == "text":
        text = content or ""
        payload.update(
            {
                "text": text,
                "preview": _short(text),
            }
        )
        return {"status": "ok", "context": payload}

    if k == "url":
        if not _is_url(content):
            return {"status": "error", "error": f"Invalid URL: {content!r}"}
        payload.update(
            {
                "url": content,
                "mime": _sniff_mime(content),
                "preview": f"URL: {content}",
            }
        )
        return {"status": "ok", "context": payload}

    # File kinds (image/video)
    if not os.path.exists(content):
        return {
            "status": "error",
            "error": f"File not found: {content!r}. Use an absolute path or put file next to the app.",
        }

    mime = _sniff_mime(content)
    payload["path"] = os.path.abspath(content)
    payload["mime"] = mime

    if k == "image":
        # Inline small images to maximize model context quality
        data_url = _inline_image_if_small(payload["path"])
        if data_url:
            payload["data_url"] = data_url
            payload["preview"] = f"Inline image ({mime}, ≤5MB)."
        else:
            payload["preview"] = f"Image path: {payload['path']} ({mime})."
        return {"status": "ok", "context": payload}

    if k == "video":
        # We don’t inline videos; just provide path + mime
        payload["preview"] = f"Video path: {payload['path']} ({mime})."
        return {"status": "ok", "context": payload}

    # Shouldn’t reach here
    return {"status": "error", "error": "Unexpected processing branch."}


async def list_context_help() -> Dict[str, Any]:
    """
    Helper: tells the model/user how to use the returned context.
    """
    return {
        "status": "ok",
        "how_to_use": (
            "Call attach_context first. The tool returns a 'context' object with kind, preview, and either "
            "text, data_url, path, or url. Pass that object verbatim to your Summarizer or task-specific agent. "
            "If it's an image and 'data_url' exists, include it in your prompt so the model can see the pixels."
        ),
        "kinds": ["text", "image", "video", "url"],
        "notes": [
            "Small images (≤5MB) are inlined as data URLs for better multimodal reasoning.",
            "Videos are referenced by path; downstream agent can extract frames if needed.",
        ],
    }


# Register as ADK tools (no kwargs; your ADK build infers name & schema from function)
AttachContextTool = FunctionTool(func=attach_context)
ListContextHelpTool = FunctionTool(func=list_context_help)
