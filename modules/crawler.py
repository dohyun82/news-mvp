from __future__ import annotations

from typing import Dict, List

from .config import get_default_keywords_by_category
from .curation import curate


def crawl_naver_news(keywords: List[str]) -> List[Dict[str, str]]:
    """
    Collect news by keywords. MVP phase uses stubbed data; replace with
    real crawling (requests/feeds) later.

    Returns curated list with categories and basic dedup/filters applied.
    """

    print("crawler.py: crawl_naver_news() called")

    # TODO: Replace stub with actual crawling using the provided keywords.
    raw_articles: List[Dict[str, str]] = [
        {"title": "현대백화점그룹, 식권대장과 협력 강화", "url": "http://example.com/a"},
        {"title": "기업 복지 포인트, 이커머스와 연계 확대", "url": "http://example.com/b"},
        {"title": "[광고] 최고의 프로모션 소식", "url": "http://example.com/c"},
        {"title": "현대백화점그룹, 식권대장과 협력 강화", "url": "http://example.com/a-dup"},
        {"title": "밀키트 수요 증가와 푸드테크 트렌드", "url": "http://example.com/d"},
    ]

    keywords_by_category = get_default_keywords_by_category()
    result = curate(raw_articles, keywords_by_category)
    return result


