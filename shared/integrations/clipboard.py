"""
Purpose: 선택된 뉴스를 그룹웨어 게시판에 복붙할 수 있는 텍스트/HTML로 포맷.

Why: 슬랙/팀즈 발송 대신, 검토 완료된 뉴스를 카테고리별로 정리해 복사한다.

How: core.categories의 순서대로 그룹화하고, 카테고리 헤더(이모지+이름) +
제목(HTML은 굵은 링크) + 요약(하위 들여쓰기)을 plain/HTML 두 형태로 생성한다.
맨 끝에 안내 푸터를 붙인다. 형광펜 강조는 게시판에서 수동으로 한다.
"""

from __future__ import annotations

import html as html_lib
from typing import Dict, List

from core.categories import (
    NEWS_CATEGORIES,
    CATEGORY_ICONS,
    UNCATEGORIZED,
    CLIPBOARD_FOOTER,
)


def _group_by_category(articles: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    grouped: Dict[str, List[Dict[str, str]]] = {}
    for a in articles:
        cat = a.get("category", UNCATEGORIZED)
        grouped.setdefault(cat, []).append(a)
    return grouped


def _ordered_categories(grouped: Dict[str, List]) -> List[str]:
    """정의된 카테고리 순서대로(비어있지 않은 것만). 미분류는 맨 끝."""
    cats = [c for c in NEWS_CATEGORIES if grouped.get(c)]
    if grouped.get(UNCATEGORIZED):
        cats.append(UNCATEGORIZED)
    return cats


def format_clipboard_text(articles: List[Dict[str, str]]) -> str:
    """그룹웨어 게시판 복붙용 일반 텍스트 (이모지 헤더 + 제목/URL/요약)."""
    if not articles:
        return "선택된 기사가 없습니다."

    grouped = _group_by_category(articles)
    lines: List[str] = []
    for cat in _ordered_categories(grouped):
        icon = CATEGORY_ICONS.get(cat, "")
        lines.append(f"{icon} {cat}".strip())
        for art in grouped[cat]:
            title = (art.get("title") or "").strip()
            url = (art.get("url") or "").strip()
            detail = (art.get("summary") or art.get("description") or "").strip()
            lines.append(f"• {title}")
            if url:
                lines.append(f"  {url}")
            if detail:
                lines.append(f"  ○ {detail}")
        lines.append("")
    lines.append(CLIPBOARD_FOOTER)
    return "\n".join(lines).strip()


def format_clipboard_html(articles: List[Dict[str, str]]) -> str:
    """리치텍스트 에디터(그룹웨어)용 HTML. 제목=굵은 링크, 요약=하위 목록."""
    if not articles:
        return "<p>선택된 기사가 없습니다.</p>"

    grouped = _group_by_category(articles)
    parts: List[str] = []
    for cat in _ordered_categories(grouped):
        icon = CATEGORY_ICONS.get(cat, "")
        header = html_lib.escape(f"{icon} {cat}".strip())
        parts.append(f"<h3>{header}</h3>")
        parts.append("<ul>")
        for art in grouped[cat]:
            title = html_lib.escape((art.get("title") or "").strip())
            url = (art.get("url") or "").strip()
            detail = html_lib.escape((art.get("summary") or art.get("description") or "").strip())
            if url and title:
                item = f'<a href="{html_lib.escape(url, quote=True)}"><strong>{title}</strong></a>'
            else:
                item = f"<strong>{title}</strong>" if title else html_lib.escape(url)
            if detail:
                item += f"<ul><li>{detail}</li></ul>"
            parts.append(f"<li>{item}</li>")
        parts.append("</ul>")
    parts.append(f"<p>{html_lib.escape(CLIPBOARD_FOOTER)}</p>")
    return "\n".join(parts)


__all__ = ["format_clipboard_text", "format_clipboard_html"]
