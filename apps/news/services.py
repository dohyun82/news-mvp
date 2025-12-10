"""
Purpose: Business logic for news clipping application.

Why: Centralize news collection, curation, and keyword management logic.

How: Integrates crawler, curation, and keyword_store modules while maintaining
backward compatibility during gradual migration.
"""

from __future__ import annotations

from typing import Dict, List, Optional

# 점진적 마이그레이션 중: 기존 modules를 import하여 사용
import sys
from pathlib import Path

# modules 디렉토리를 sys.path에 추가 (점진적 마이그레이션 중)
modules_path = Path(__file__).parent.parent.parent / "modules"
if str(modules_path) not in sys.path:
    sys.path.insert(0, str(modules_path))

from modules import crawler, keyword_store
from modules.curation import curate


def collect_news(
    keywords: Optional[List[str]] = None,
    user_keywords: Optional[str] = None,
    user_max_articles: Optional[int] = None,
    user_category_keywords: Optional[Dict[str, List[str]]] = None,
    user_max_age_hours: Optional[int] = None
) -> List[Dict[str, str]]:
    """Collect news articles using configured keywords.
    
    Args:
        keywords: Legacy keyword list (for backward compatibility)
        user_keywords: User-configured keywords (comma-separated string, highest priority)
        user_max_articles: User-configured max articles (highest priority)
        user_category_keywords: User-configured category keywords (highest priority)
        user_max_age_hours: User-configured max age in hours (highest priority)
        
    Returns:
        List of curated articles with categories
    """
    return crawler.crawl_naver_news(
        keywords=keywords or [],
        user_keywords=user_keywords,
        user_max_articles=user_max_articles,
        user_category_keywords=user_category_keywords,
        user_max_age_hours=user_max_age_hours
    )


def get_keyword_settings() -> Dict:
    """Get current keyword settings from keyword_store.
    
    Returns:
        Dictionary containing query_keywords, category_keywords, max_articles, max_age_hours
    """
    return {
        "keywords": keyword_store.get_query_keywords(),
        "max_articles": keyword_store.get_max_articles(),
        "category_keywords": keyword_store.get_category_keywords(),
        "max_age_hours": keyword_store.get_max_age_hours(),
    }


def save_keyword_settings(
    keywords: Optional[str] = None,
    max_articles: Optional[int] = None,
    category_keywords: Optional[Dict[str, List[str]]] = None,
    max_age_hours: Optional[int] = None
) -> bool:
    """Save keyword settings to keyword_store.
    
    Args:
        keywords: Query keywords (comma-separated string)
        max_articles: Maximum articles to collect
        category_keywords: Category-specific keywords dictionary
        max_age_hours: Maximum article age in hours
        
    Returns:
        True if successful, False otherwise
    """
    return keyword_store.update_all(
        query_keywords=keywords,
        category_keywords=category_keywords,
        max_articles=max_articles,
        max_age_hours=max_age_hours
    )


__all__ = [
    "collect_news",
    "get_keyword_settings",
    "save_keyword_settings",
]
