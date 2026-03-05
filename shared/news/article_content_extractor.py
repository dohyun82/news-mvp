"""
Article content extraction helper for news summarization.

This module fetches article HTML by URL and extracts readable text for AI
summarization. It prefers trafilatura and falls back to a lightweight parser
to keep the flow resilient.
"""

from __future__ import annotations

import html
import logging
import re
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass

try:
    import trafilatura  # type: ignore
except Exception:  # pragma: no cover - handled at runtime
    trafilatura = None

from core.config import ArticleFetchConfig


_SCRIPT_STYLE_RE = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"[ \t]+")
_BLANK_LINES_RE = re.compile(r"\n{3,}")
_BLOCKED_HTTP_CODES = {401, 403, 404, 410, 451}


@dataclass(frozen=True)
class ExtractResult:
    text: str
    status: str
    source: str
    error: str = ""


def _normalize_text(text: str, max_chars: int) -> str:
    cleaned = html.unescape(text or "")
    cleaned = cleaned.replace("\r", "\n")
    cleaned = _SPACE_RE.sub(" ", cleaned)
    cleaned = "\n".join(line.strip() for line in cleaned.split("\n"))
    cleaned = _BLANK_LINES_RE.sub("\n\n", cleaned)
    cleaned = cleaned.strip()
    if max_chars > 0 and len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars].rstrip()
    return cleaned


def _fallback_extract_text(html_text: str, max_chars: int) -> str:
    stripped = _SCRIPT_STYLE_RE.sub(" ", html_text)
    stripped = _TAG_RE.sub(" ", stripped)
    return _normalize_text(stripped, max_chars)


def _is_timeout_error(exc: Exception) -> bool:
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return True
    msg = str(exc).lower()
    return "timed out" in msg or "timeout" in msg


def extract_article_content(url: str) -> ExtractResult:
    """Fetch and extract article text from URL.

    Returns ExtractResult with status:
    - ok
    - timeout
    - blocked
    - parse_failed
    - empty
    """
    cfg = ArticleFetchConfig()
    if not cfg.enabled:
        return ExtractResult(text="", status="parse_failed", source="fallback", error="article fetch disabled")

    logger = logging.getLogger("news.extractor")
    html_text = ""

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "news-mvp-bot/1.0",
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        with urllib.request.urlopen(req, timeout=cfg.timeout_seconds) as resp:
            raw = resp.read()
            charset = "utf-8"
            if hasattr(resp, "headers") and resp.headers is not None:
                try:
                    charset = resp.headers.get_content_charset() or "utf-8"
                except Exception:
                    charset = "utf-8"
        html_text = raw.decode(charset, errors="ignore")
    except urllib.error.HTTPError as exc:
        status = "blocked" if exc.code in _BLOCKED_HTTP_CODES else "parse_failed"
        return ExtractResult(text="", status=status, source="fallback", error=f"HTTPError {exc.code}")
    except urllib.error.URLError as exc:
        reason = str(exc.reason) if getattr(exc, "reason", None) is not None else str(exc)
        if _is_timeout_error(exc):
            return ExtractResult(text="", status="timeout", source="fallback", error=reason[:200])
        return ExtractResult(text="", status="parse_failed", source="fallback", error=reason[:200])
    except Exception as exc:
        status = "timeout" if _is_timeout_error(exc) else "parse_failed"
        return ExtractResult(
            text="",
            status=status,
            source="fallback",
            error=f"{type(exc).__name__}: {str(exc)[:200]}",
        )

    if not html_text.strip():
        return ExtractResult(text="", status="empty", source="fallback", error="empty html response")

    if trafilatura is not None:
        try:
            extracted = trafilatura.extract(
                html_text,
                include_comments=False,
                include_tables=False,
                favor_precision=True,
                deduplicate=True,
            )
            normalized = _normalize_text(extracted or "", cfg.text_max_chars)
            if normalized:
                return ExtractResult(text=normalized, status="ok", source="trafilatura")
        except Exception as exc:
            logger.warning("trafilatura extract failed for %s: %s", url, exc)

    fallback = _fallback_extract_text(html_text, cfg.text_max_chars)
    if fallback:
        return ExtractResult(text=fallback, status="ok", source="fallback")
    return ExtractResult(text="", status="empty", source="fallback", error="no readable text extracted")
