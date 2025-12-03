"""
Purpose: Centralized configuration and domain constants for NewsBot.

Why: Provide single sources of truth for API keys and environment-driven settings.
Keywords are now managed via keyword_store module (JSON file-based), not environment variables.

How: Load environment variables using python-dotenv when available, expose
typed accessors. Keywords are accessed via keyword_store module.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List

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


def get_default_keywords_by_category() -> Dict[str, List[str]]:
    """Return the mapping of category → keywords.
    
    Categories follow the product domain:
    - 그룹사 뉴스
    - 업계 뉴스
    - 참고 뉴스
    - 읽을 거리 (no fixed keywords; handled as catch-all)
    
    Note: This function now uses keyword_store module (JSON file-based) instead
    of environment variables. This maintains backward compatibility for existing
    code that calls this function.
    
    Returns:
        카테고리별 키워드 딕셔너리
    """
    # keyword_store 모듈을 동적으로 import하여 순환 참조 방지
    from . import keyword_store
    return keyword_store.get_category_keywords()


__all__ = [
    "SlackConfig",
    "OpenAIConfig",
    "RealDataConfig",
    "get_default_keywords_by_category",
]


