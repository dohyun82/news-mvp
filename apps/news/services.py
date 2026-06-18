"""
Purpose: Business logic for news clipping application.

Why: Centralize news collection and keyword management logic.

How: Integrates crawler, curation, and keyword_store modules. 카테고리 분류는
검토 화면에서 수동으로 하므로 키워드는 단일 수집용 풀로만 관리한다.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from modules import crawler, keyword_store


def collect_news(
    keywords: Optional[List[str]] = None,
    user_keywords: Optional[str] = None,
    user_max_articles: Optional[int] = None,
    user_max_age_hours: Optional[int] = None,
) -> List[Dict[str, str]]:
    """Collect news articles using configured keywords.

    Args:
        keywords: Legacy keyword list (for backward compatibility)
        user_keywords: User-configured keywords (comma-separated string)
        user_max_articles: User-configured max articles
        user_max_age_hours: User-configured max age in hours

    Returns:
        List of curated articles (all '미분류'; 분류는 검토 화면에서 수동 지정).
    """
    return crawler.crawl_naver_news(
        keywords=keywords or [],
        user_keywords=user_keywords,
        user_max_articles=user_max_articles,
        user_max_age_hours=user_max_age_hours,
    )


def get_keyword_settings() -> Dict:
    """Get current keyword settings from keyword_store.

    Returns:
        Dictionary containing keywords, max_articles, max_age_hours
    """
    return {
        "keywords": keyword_store.get_query_keywords(),
        "max_articles": keyword_store.get_max_articles(),
        "max_age_hours": keyword_store.get_max_age_hours(),
    }


def save_keyword_settings(
    keywords: Optional[str] = None,
    max_articles: Optional[int] = None,
    max_age_hours: Optional[int] = None,
) -> bool:
    """Save keyword settings to keyword_store.

    Args:
        keywords: Query keywords (comma-separated string)
        max_articles: Maximum articles to collect
        max_age_hours: Maximum article age in hours

    Returns:
        True if successful, False otherwise
    """
    return keyword_store.update_all(
        query_keywords=keywords,
        max_articles=max_articles,
        max_age_hours=max_age_hours,
    )


__all__ = [
    "collect_news",
    "get_keyword_settings",
    "save_keyword_settings",
]
