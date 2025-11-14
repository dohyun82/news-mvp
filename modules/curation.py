"""
Purpose: Curation utilities - keyword to category mapping, de-duplication,
and basic ad/noise filtering for collected news items.

Why: Keep business curation rules centralized and testable.

How: Provide pure functions operating on simple dictionaries so that the
state store/backend delivery can remain decoupled.
"""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Tuple


def normalize_title(title: str) -> str:
    """Normalize article titles for comparison (case/punctuation).

    - Lowercase
    - Remove brackets/dashes
    - Collapse consecutive whitespace
    """

    lowered = title.lower()
    # Remove bracket/dash characters without introducing extra spaces first
    no_brackets = re.sub(r"[\[\]\(\)\{\}\-–—]", "", lowered)
    # Then collapse all whitespace runs to a single space
    cleaned = re.sub(r"\s+", " ", no_brackets).strip()
    return cleaned


def map_category(title: str, keywords_by_category: Dict[str, List[str]]) -> str:
    """Map a title to a category using a simple keyword presence heuristic.

    If multiple categories match, the first defined in the mapping wins.
    If none match, return "읽을거리" as a catch-all.
    """

    t = title.lower()
    for category, keywords in keywords_by_category.items():
        for kw in keywords:
            if kw.lower() in t:
                return category
    return "읽을거리"


def is_advertorial(title: str) -> bool:
    """Basic advertorial/noise filter based on simple cue words.

    Note: This is a placeholder. Real implementations may leverage source,
    NLP cues, or more robust heuristics.
    """

    cues = [
        "광고",
        "협찬",
        "제휴",
        "프로모션",
    ]
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
        
        # URL이 있으면 URL 기준으로 중복 체크
        # 같은 URL이면 제목이 달라도 같은 기사로 간주
        if url and url in seen_urls:
            continue
        
        # 제목 기준 중복 체크
        # 정규화된 제목이 같으면 같은 기사로 간주
        if norm_title and norm_title not in seen_titles:
            seen_titles.add(norm_title)
            if url:
                seen_urls.add(url)
            result.append(art)
    return result


def curate(articles: Iterable[Dict[str, str]], keywords_by_category: Dict[str, List[str]]) -> List[Dict[str, str]]:
    """Apply 1) advertorial filter 2) dedup 3) category mapping.

    Each output item will include a 'category' field.
    """

    filtered = [a for a in articles if not is_advertorial(a.get("title", ""))]
    unique = deduplicate(filtered)
    curated: List[Dict[str, str]] = []
    for a in unique:
        category = map_category(a.get("title", ""), keywords_by_category)
        a2 = {**a, "category": category}
        curated.append(a2)
    return curated


__all__ = [
    "normalize_title",
    "map_category",
    "is_advertorial",
    "deduplicate",
    "curate",
]


