"""
Purpose: Curation utilities - de-duplication and basic ad/noise filtering for
collected news items.

Why: Keep business curation rules centralized and testable.

How: 순수 함수로 단순 딕셔너리를 다룬다. 카테고리 분류는 검토 화면에서 사람이
수동으로 하므로, curate는 모든 기사를 '미분류'로 둔다(자동 분류 없음).
중복 판단은 정규화된 URL과 정규화된 제목을 함께 사용한다.
"""

from __future__ import annotations

import re
from typing import Dict, Iterable, List
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

from core.categories import UNCATEGORIZED


# 뉴스의 '형식'을 나타내는 말머리 태그(주체명이 아님) — 비교 시에만 제거한다.
# 예: "[속보] 현대백화점 …" 과 "현대백화점 …" 을 같은 기사로 보기 위함.
# 주의: "[현대백화점그룹]" 같은 주체명 말머리는 보존해야 하므로 화이트리스트로만 제거.
_LEAD_TAGS = {
    "속보", "단독", "종합", "전문", "화보", "영상", "인터뷰", "기고", "칼럼",
    "사설", "오피니언", "포토", "줌인", "르포", "현장", "공식", "팩트체크",
    "일문일답", "업데이트", "핫이슈", "이슈", "분석",
}

# URL 비교 시 무시할 추적/캠페인 파라미터(기사 식별과 무관).
_TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "ref", "referrer", "fbclid", "gclid", "igshid", "spm",
}


def _strip_lead_tags(text: str) -> str:
    """맨 앞의 형식 말머리([속보],【종합2보】 등)만 제거. 주체명 말머리는 보존."""
    while True:
        m = re.match(r"^\s*[\[\【]\s*([^\]\】]*?)\s*[\]\】]\s*", text)
        if not m:
            break
        inner = m.group(1)
        base = re.sub(r"\d+\S*$", "", inner).strip()  # '종합2보' -> '종합'
        if inner in _LEAD_TAGS or base in _LEAD_TAGS:
            text = text[m.end():]
        else:
            break
    return text


def normalize_title(title: str) -> str:
    """Normalize article titles for comparison (case/punctuation).

    - 형식 말머리([속보][단독] 등) 제거 (주체명 말머리는 보존)
    - Lowercase
    - Remove brackets/dashes/quotes/middle-dots
    - Collapse consecutive whitespace
    """

    lowered = title.lower()
    no_lead = _strip_lead_tags(lowered)
    no_sym = re.sub(r"[\[\]\(\)\{\}\-–—·…\"'“”‘’]", "", no_lead)
    cleaned = re.sub(r"\s+", " ", no_sym).strip()
    return cleaned


def normalize_url(url: str) -> str:
    """Normalize URLs for duplicate comparison.

    - scheme http/https -> https 로 통일
    - host 소문자화, www./m. 접두 제거
    - 추적 파라미터(utm_* 등) 제거, 나머지 쿼리는 보존하고 정렬
    - fragment 및 끝 슬래시 제거

    주의: 쿼리 전체를 지우면 같은 사이트의 다른 기사(?idxno=1 vs ?idxno=2)를
    같다고 오판하므로, 추적 파라미터만 선별 제거한다.
    """

    raw = (url or "").strip()
    if not raw:
        return ""
    try:
        parts = urlsplit(raw)
    except ValueError:
        return raw
    if not parts.netloc:
        # 스킴 없는 상대경로 등은 원본 그대로 비교
        return raw

    scheme = "https" if parts.scheme in ("http", "https", "") else parts.scheme
    host = parts.netloc.lower()
    for prefix in ("www.", "m."):
        if host.startswith(prefix):
            host = host[len(prefix):]
            break
    if host.endswith(":80"):
        host = host[:-3]
    elif host.endswith(":443"):
        host = host[:-4]

    query_pairs = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if k.lower() not in _TRACKING_PARAMS
    ]
    query_pairs.sort()
    query = urlencode(query_pairs)
    path = parts.path.rstrip("/")
    return urlunsplit((scheme, host, path, query, ""))


def is_advertorial(title: str) -> bool:
    """Basic advertorial/noise filter based on simple cue words."""

    cues = ["광고", "협찬", "제휴", "프로모션"]
    lt = title.lower()
    return any(cue in lt for cue in cues)


def deduplicate(articles: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
    """Deduplicate articles by normalized title and URL.

    중복 판단 기준:
    1. 정규화된 URL이 같으면 같은 기사로 간주 (http/https·www·추적파라미터 차이 흡수)
    2. 정규화된 제목이 같으면 같은 기사로 간주 (형식 말머리·기호·공백 차이 흡수)

    Keep the first occurrence.
    """

    seen_titles = set()
    seen_urls = set()
    result: List[Dict[str, str]] = []
    for art in articles:
        url = normalize_url(art.get("url", ""))
        norm_title = normalize_title(art.get("title", ""))

        if url and url in seen_urls:
            continue

        if norm_title and norm_title not in seen_titles:
            seen_titles.add(norm_title)
            if url:
                seen_urls.add(url)
            result.append(art)
    return result


def dedupe_keywords(keywords: Iterable[str]) -> List[str]:
    """검색 키워드의 중복을 수집 전에 제거한다(중복 수집·API 호출 감소).

    - (A) 표기 변형: 공백/대소문자만 다른 키워드는 첫 등장만 유지
    - (B) 포함관계: 더 짧은 키워드가 다른 키워드에 부분 포함되면 긴 쪽(하위어)을
      제거한다. 짧은 상위어 검색이 하위어 결과를 대체로 포섭하기 때문이다.

    설정에 등록된 키워드 목록 자체는 보존하고, 이 함수는 수집 시점에만 적용한다.
    원래 등장 순서를 유지한다.
    """

    # (A) 표기 변형(공백/대소문자) 제거 — 첫 등장만 유지
    seen = set()
    staged: List[str] = []
    for k in keywords:
        k = (k or "").strip()
        if not k:
            continue
        n = k.replace(" ", "").lower()
        if n in seen:
            continue
        seen.add(n)
        staged.append(k)

    # (B) 포함관계 하위어 제거 — 더 짧은 상위어가 있으면 긴 하위어를 버린다
    norms = [(k, k.replace(" ", "").lower()) for k in staged]
    result: List[str] = []
    for k, n in norms:
        covered = any(on != n and on in n and len(on) < len(n) for _, on in norms)
        if not covered:
            result.append(k)
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
    "normalize_url",
    "is_advertorial",
    "deduplicate",
    "dedupe_keywords",
    "curate",
]
