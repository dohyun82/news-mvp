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

    load_dotenv()
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
    max_articles: int = int(os.getenv("NAVER_MAX_ARTICLES", "20"))
    timeout_ms: int = int(os.getenv("NAVER_TIMEOUT_MS", "5000"))
    sort: str = os.getenv("NAVER_SORT", "sim")
    delay_ms: int = int(os.getenv("NAVER_DELAY_MS", "300"))


# Domain: Category → Keywords mapping (from Confluence definitions)
GROUP_NEWS_KEYWORDS: List[str] = [
    "현대이지웰",
    "현대백화점",
    "현대백화점그룹",
    "현대그린푸드",
    "식권대장",
    "복지대장",
    "vendys",
    "조정호",
    "현대벤디스",
]

INDUSTRY_NEWS_KEYWORDS: List[str] = [
    "모바일 식권",
    "전자 식권",
    "식권 앱",
    "식권 플랫폼",
    "식대 정산",
    "식대 지원",
    "기업 복지",
    "복지 포인트",
    "복지몰",
    "배달 앱",
    "배달 플랫폼",
    "이커머스",
    "간편식",
    "밀키트",
    "푸드테크",
]

REFERENCE_NEWS_KEYWORDS: List[str] = [
    "MRO",
    "기업 문화",
    "사무실",
    "업무 공간",
    "워크플레이스",
    "오피스",
]


def get_default_keywords_by_category() -> Dict[str, List[str]]:
    """Return the default mapping of category → keywords.

    Categories follow the product domain:
    - 그룹사 뉴스
    - 업계 뉴스
    - 참고 뉴스
    - 읽을 거리 (no fixed keywords; handled as catch-all)
    """

    return {
        "그룹사": GROUP_NEWS_KEYWORDS,
        "업계": INDUSTRY_NEWS_KEYWORDS,
        "참고": REFERENCE_NEWS_KEYWORDS,
        # "읽을거리": []  # explicitly left without keywords by design
    }


__all__ = [
    "SlackConfig",
    "GeminiConfig",
    "RealDataConfig",
    "get_default_keywords_by_category",
    "GROUP_NEWS_KEYWORDS",
    "INDUSTRY_NEWS_KEYWORDS",
    "REFERENCE_NEWS_KEYWORDS",
]


