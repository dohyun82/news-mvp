"""
Purpose: 선택된 뉴스를 그룹웨어 게시판에 복붙할 수 있는 텍스트/HTML로 포맷.

Why: 슬랙/팀즈 발송 대신, 검토 완료된 뉴스를 카테고리별로 정리해 복사한다.

How: core.categories의 순서대로 그룹화하고 유니코드 이모지 + 제목/URL/요약을
plain text와 HTML 두 형태로 생성한다(그룹웨어 에디터에 따라 적용).
"""

from __future__ import annotations

import html as html_lib
from typing import Dict, List

from core.categories import NEWS_CATEGORIES, CATEGORY_ICONS, UNCATEGORIZED


def _group_by_category(articles: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    grouped: Dict[str, List[Dict[str, str]]] = {}
    for a in articles:
        cat = a.get("category", UNCATEGORIZED)
        grouped.setdefault(cat, []).append(a)
    return grouped


def _ordered_categories(grouped: Dict[str, List]) -> List[str]:
    """정의된 5개 순서대로, 비어있지 않은 것만. 미분류는 맨 끝."""
    cats = [c for c in NEWS_CATEGORIES if grouped.get(c)]
    if grouped.get(UNCATEGORIZED):
        cats.append(UNCATEGORIZED)
    return cats


def format_clipboard_text(articles: List[Dict[str, str]]) -> str:
    """그룹웨어 게시판 복붙용 일반 텍스트 (실제 이모지 + 카테고리별 정리)."""
    if not articles:
        return "선택된 기사가 없습니다."

    grouped = _group_by_category(articles)
    lines: List[str] = []
    for cat in _ordered_categories(grouped):
        icon = CATEGORY_ICONS.get(cat, "")
        lines.append(f"[{icon} {cat}]".replace("[ ", "["))
        for art in grouped[cat]:
            title = (art.get("title") or "").strip()
            url = (art.get("url") or "").strip()
            detail = (art.get("summary") or art.get("description") or "").strip()
            lines.append(f"- {title}")
            if url:
                lines.append(f"  {url}")
            if detail:
                lines.append(f"  {detail}")
        lines.append("")
    return "\n".join(lines).strip()


def format_clipboard_html(articles: List[Dict[str, str]]) -> str:
    """리치텍스트 에디터(그룹웨어)용 HTML. 붙여넣으면 서식이 유지된다."""
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
                item = f'<a href="{html_lib.escape(url, quote=True)}">{title}</a>'
            else:
                item = title or html_lib.escape(url)
            if detail:
                item += f"<br>{detail}"
            parts.append(f"<li>{item}</li>")
        parts.append("</ul>")
    return "\n".join(parts)


__all__ = ["format_clipboard_text", "format_clipboard_html"]
