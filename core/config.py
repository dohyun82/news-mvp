"""
Purpose: Centralized configuration and domain constants for vendys-ai-automation-platform.

Why: Provide single sources of truth for API keys and environment-driven settings.
Keywords are now managed via keyword_store module (JSON file-based), not environment variables.

How: Load environment variables using python-dotenv when available, expose
typed accessors. Keywords are accessed via keyword_store module.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

try:
    # Optional: present in requirements; safe to import.
    from dotenv import load_dotenv  # type: ignore
    from pathlib import Path

    # .env 파일 경로를 명시적으로 지정 (프로젝트 루트 기준)
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)
except Exception:
    # If dotenv is unavailable or fails, proceed with OS environment only.
    pass


@dataclass(frozen=True)
class SlackConfig:
    """Configuration values for Slack delivery.

    Note: Values can be empty during early development. Validation should be
    performed right before making external requests.
    """

    bot_token: str = os.getenv("SLACK_BOT_TOKEN", "")
    channel_id: str = os.getenv("SLACK_CHANNEL_ID", "")


@dataclass(frozen=True)
class OpenAIConfig:
    """Configuration values for the summarization provider (e.g., OpenAI)."""

    api_key: str = os.getenv("OPENAI_API_KEY", "")
    model: str = os.getenv("OPENAI_MODEL", "gpt-5.4")


@dataclass(frozen=True)
class ArticleFetchConfig:
    """Configuration values for article content fetching/extraction."""

    enabled: bool = os.getenv("ARTICLE_FETCH_ENABLED", "true").lower() == "true"
    timeout_seconds: int = int(os.getenv("ARTICLE_FETCH_TIMEOUT_SECONDS", "5"))
    text_max_chars: int = int(os.getenv("ARTICLE_TEXT_MAX_CHARS", "4000"))


@dataclass(frozen=True)
class RealDataConfig:
    """Configuration for real data fetching via Naver Search API.
    
    Note: Keywords (query_keywords, category_keywords), max_articles, and
    max_age_hours are now managed via keyword_store module (JSON file-based),
    not environment variables. This class only contains API credentials and
    technical settings (timeout, sort, delay).
    """

    enabled: bool = os.getenv("REALDATA_ENABLED", "false").lower() == "true"
    client_id: str = os.getenv("NAVER_API_CLIENT_ID", "")
    client_secret: str = os.getenv("NAVER_API_CLIENT_SECRET", "")
    timeout_ms: int = int(os.getenv("NAVER_TIMEOUT_MS", "5000"))
    sort: str = os.getenv("NAVER_SORT", "sim")
    delay_ms: int = int(os.getenv("NAVER_DELAY_MS", "300"))
    log_each_item: bool = os.getenv("NAVER_LOG_EACH_ITEM", "false").lower() == "true"


__all__ = [
    "SlackConfig",
    "OpenAIConfig",
    "ArticleFetchConfig",
    "RealDataConfig",
]
