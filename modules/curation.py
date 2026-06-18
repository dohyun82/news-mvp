"""
Purpose: Curation utilities - de-duplication and basic ad/noise filtering for
collected news items.

Why: Keep business curation rules centralized and testable.

How: 순수 함수로 단순 딕셔너리를 다룬다. 카테고리 분류는 검토 화면에서 사람이
수동으로 하므로, curate는 모든 기사를 '미분류'로 둔다(자동 분류 없음).
"""

from __future__ import annotations

import re
from typing import Dict, Iterable, List

from core.categories import UNCATEGORIZED


def normalize_title(title: str) -> str:
    """Normalize article titles for comparison (case/punctuation).

    - Lowercase
    - Remove brackets/dashes
    - Collapse consecutive whitespace
    """

    lowered = title.lower()
    no_brackets = re.sub(r"[\[\]\(\)\{\}\-–—]", "", lowered)
    cleaned = re.sub(r"\s+", " ", no_brackets).strip()
    return cleaned


def is_advertorial(title: str) -> bool:
    """Basic advertorial/noise filter based on simple cue words."""

    cues = ["광고", "협찬", "제휴", "프로모션"]
    lt = title.lower()
    return any(cue in lt for cue in cues)


def deduplicate(articles: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
    """Deduplicate articles by normalized title and URL.

    중복 판단 기준:
    1. URL이 있으면 URL 기준으로 중복 체크 (같은 URL이면 같은 기사로 간주)
    2. 제목 기준으로도 중복 체크 (정규화된 제목이 같으면 같은 기사로 간주)

    Keep the first occurrence.
    """

    seen_titles = set()
    seen_urls = set()
    result: List[Dict[str, str]] = []
    for art in articles:
        url = art.get("url", "").strip()
        norm_title = normalize_title(art.get("title", ""))

        if url and url in seen_urls:
            continue

        if norm_title and norm_title not in seen_titles:
            seen_titles.add(norm_title)
            if url:
                seen_urls.add(url)
            result.append(art)
    return result


def curate(articles: Iterable[Dict[str, str]], keywords_by_category=None) -> List[Dict[str, str]]:
    """광고 필터 + 중복 제거를 적용하고 카테고리를 '미분류'로 부여한다.

    실제 카테고리 분류는 검토 화면에서 사람이 수동으로 지정한다.
    keywords_by_category 인자는 하위 호환을 위해 남겨두며 사용하지 않는다.
    """

    filtered = [a for a in articles if not is_advertorial(a.get("title", ""))]
    unique = deduplicate(filtered)
    return [{**a, "category": UNCATEGORIZED} for a in unique]


__all__ = [
    "normalize_title",
    "is_advertorial",
    "deduplicate",
    "curate",
]
