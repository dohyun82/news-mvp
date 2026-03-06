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
    model: str = os.getenv("OPENAI_MODEL", "gpt-5.4")


@dataclass(frozen=True)
class ArticleFetchConfig:
    """Configuration values for article content fetching/extraction."""

    enabled: bool = os.getenv("ARTICLE_FETCH_ENABLED", "true").lower() == "true"
    timeout_seconds: int = int(os.getenv("ARTICLE_FETCH_TIMEOUT_SECONDS", "5"))
    text_max_chars: int = int(os.getenv("ARTICLE_TEXT_MAX_CHARS", "4000"))


@dataclass(frozen=True)
class DatadogConfig:
    """Configuration values for Datadog API integration.
    
    Used for log analysis functionality to query mobile app server/client logs.
    """

    api_key: str = os.getenv("DATADOG_API_KEY", "")
    app_key: str = os.getenv("DATADOG_APP_KEY", "")
    site: str = os.getenv("DATADOG_SITE", "datadoghq.com")  # 기본값: US1


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
    # modules/keyword_store.py는 아직 유지되므로 상대 경로로 import
    import sys
    from pathlib import Path
    
    # modules 디렉토리를 sys.path에 추가 (점진적 마이그레이션 중)
    modules_path = Path(__file__).parent.parent / "modules"
    if str(modules_path) not in sys.path:
        sys.path.insert(0, str(modules_path))
    
    from modules import keyword_store
    return keyword_store.get_category_keywords()


__all__ = [
    "SlackConfig",
    "OpenAIConfig",
    "ArticleFetchConfig",
    "DatadogConfig",
    "RealDataConfig",
    "get_default_keywords_by_category",
]
