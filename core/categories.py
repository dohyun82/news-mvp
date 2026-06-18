"""
Purpose: 뉴스 카테고리 단일 진실 공급원(SSOT).

Why: 카테고리가 라우트·템플릿·복붙 포맷 등 여러 곳에 하드코딩되어 변경 시
누락/불일치가 발생했다. 정의를 이 모듈 한 곳에 모으고 모든 코드가 참조한다.

How: 고정 도메인 상수이므로(런타임 사용자 편집 없음) JSON이 아닌 코드 상수로
관리한다. 카테고리가 또 바뀌면 이 파일만 수정하면 된다.
"""

from __future__ import annotations

from typing import Dict, List

# 미분류: 수집 직후 기본 상태. 검토 화면에서 사람이 5개 중 하나로 분류한다.
UNCATEGORIZED = "미분류"

# 발행 순서대로 정의된 5개 카테고리 (검토 화면 드롭존·복붙 출력 순서)
NEWS_CATEGORIES: List[str] = [
    "그룹사",
    "유통·F&B·급식",
    "플랫폼·테크",
    "경쟁사·복지·HR 트렌드",
    "시장·소비 트렌드",
    "읽을거리",
]

# 복붙(그룹웨어 게시판)용 유니코드 이모지. 슬랙 :emoji: 문법이 아닌 실제 문자.
CATEGORY_ICONS: Dict[str, str] = {
    "그룹사": "💚",
    "유통·F&B·급식": "🍿",
    "플랫폼·테크": "🛠️",
    "경쟁사·복지·HR 트렌드": "🔍",
    "시장·소비 트렌드": "💸",
    "읽을거리": "🌐",
}

# DOM id 등 식별자용 슬러그. 카테고리명에 가운뎃점(·)·공백이 있어
# id에 직접 쓰면 깨지기 쉬우므로 인덱스 기반 슬러그를 별도로 둔다.
CATEGORY_SLUGS: Dict[str, str] = {
    cat: f"cat-{i}" for i, cat in enumerate(NEWS_CATEGORIES)
}

# 복붙(그룹웨어 게시판) 맨 끝에 붙는 안내 푸터
CLIPBOARD_FOOTER = (
    "★ 뉴스 클리핑 관련 의견, 업계 키워드 추천, 보고 싶은 주제가 있다면 "
    "댓글로 자유롭게 남겨주세요. 더 유익한 클리핑 운영에 큰 도움이 됩니다!"
)


def is_valid_category(category: str, *, allow_uncategorized: bool = True) -> bool:
    """주어진 문자열이 유효한 카테고리인지 확인한다.

    Args:
        category: 검사할 카테고리명
        allow_uncategorized: 미분류를 유효로 볼지 여부 (기본 True)
    """
    if category in NEWS_CATEGORIES:
        return True
    return allow_uncategorized and category == UNCATEGORIZED


def categories_with_meta() -> List[Dict[str, str]]:
    """템플릿 주입용: [{"name", "icon", "slug"}, ...]를 정의 순서대로 반환."""
    return [
        {"name": cat, "icon": CATEGORY_ICONS.get(cat, ""), "slug": CATEGORY_SLUGS[cat]}
        for cat in NEWS_CATEGORIES
    ]


__all__ = [
    "UNCATEGORIZED",
    "NEWS_CATEGORIES",
    "CATEGORY_ICONS",
    "CATEGORY_SLUGS",
    "CLIPBOARD_FOOTER",
    "is_valid_category",
    "categories_with_meta",
]
