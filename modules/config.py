"""
Purpose: Centralized configuration and domain constants for NewsBot.

Why: Provide single sources of truth for keywords-to-category mapping and
environment-driven settings. This enables consistent behavior across modules
without scattering magic strings.

How: Load environment variables using python-dotenv when available, expose
typed accessors and domain dictionaries (e.g., keywords per category).
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
class GeminiConfig:
    """Configuration values for the summarization provider (e.g., Gemini)."""

    api_key: str = os.getenv("GEMINI_API_KEY", "")


@dataclass(frozen=True)
class RealDataConfig:
    """Configuration for real data fetching via Naver Search API."""

    enabled: bool = os.getenv("REALDATA_ENABLED", "false").lower() == "true"
    client_id: str = os.getenv("NAVER_API_CLIENT_ID", "")
    client_secret: str = os.getenv("NAVER_API_CLIENT_SECRET", "")
    query_keywords: str = os.getenv("NAVER_QUERY_KEYWORDS", "")
    max_articles: int = int(os.getenv("NAVER_MAX_ARTICLES", "30"))
    timeout_ms: int = int(os.getenv("NAVER_TIMEOUT_MS", "5000"))
    sort: str = os.getenv("NAVER_SORT", "sim")
    delay_ms: int = int(os.getenv("NAVER_DELAY_MS", "300"))
    group_keywords: str = os.getenv("CATEGORY_GROUP_KEYWORDS", "")
    industry_keywords: str = os.getenv("CATEGORY_INDUSTRY_KEYWORDS", "")
    reference_keywords: str = os.getenv("CATEGORY_REFERENCE_KEYWORDS", "")
    max_news_age_hours: int = int(os.getenv("NEWS_MAX_AGE_HOURS", "24"))


def get_default_keywords_by_category() -> Dict[str, List[str]]:
    """Return the default mapping of category → keywords.

    Categories follow the product domain:
    - 그룹사 뉴스
    - 업계 뉴스
    - 참고 뉴스
    - 읽을 거리 (no fixed keywords; handled as catch-all)

    환경변수에서만 키워드를 읽어옵니다.
    환경변수가 없거나 빈 문자열이면 빈 리스트를 반환합니다.
    """
    cfg = RealDataConfig()
    
    def parse_keywords(env_value: str) -> List[str]:
        """환경변수 값을 파싱하여 리스트로 변환. 없으면 빈 리스트 반환."""
        if env_value and env_value.strip():
            # 쉼표로 구분된 문자열을 리스트로 변환
            return [kw.strip() for kw in env_value.split(",") if kw.strip()]
        return []
    
    return {
        "그룹사": parse_keywords(cfg.group_keywords),
        "업계": parse_keywords(cfg.industry_keywords),
        "참고": parse_keywords(cfg.reference_keywords),
        # "읽을거리": []  # explicitly left without keywords by design
    }


__all__ = [
    "SlackConfig",
    "GeminiConfig",
    "RealDataConfig",
    "get_default_keywords_by_category",
]


