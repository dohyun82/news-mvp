"""
Purpose: Minimal in-memory state store for the review workflow.

Why: Allow the app to keep collected articles, selection flags, and summaries
without introducing a database at MVP stage. The API is intentionally small
and replaceable with a DB-backed implementation later.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Article:
    title: str
    url: str
    category: str
    selected: bool = False
    summary: str = ""


class InMemoryStore:
    def __init__(self) -> None:
        self._articles: List[Article] = []

    # CRUD-ish operations
    def set_articles(self, articles: List[Dict[str, str]]) -> None:
        self._articles = [
            Article(
                title=a.get("title", ""),
                url=a.get("url", ""),
                category=a.get("category", "읽을거리"),
            )
            for a in articles
        ]

    def list_articles(self) -> List[Dict[str, str]]:
        return [
            {
                "title": a.title,
                "url": a.url,
                "category": a.category,
                "selected": a.selected,
                "summary": a.summary,
            }
            for a in self._articles
        ]

    def delete_by_url(self, url: str) -> bool:
        before = len(self._articles)
        self._articles = [a for a in self._articles if a.url != url]
        return len(self._articles) != before

    def set_selected(self, url: str, selected: bool) -> bool:
        for a in self._articles:
            if a.url == url:
                a.selected = selected
                return True
        return False

    def set_summary(self, url: str, summary: str) -> bool:
        for a in self._articles:
            if a.url == url:
                a.summary = summary
                return True
        return False

    def get_selected(self) -> List[Dict[str, str]]:
        return [
            {
                "title": a.title,
                "url": a.url,
                "category": a.category,
                "summary": a.summary,
            }
            for a in self._articles
            if a.selected
        ]


store = InMemoryStore()

__all__ = ["Article", "InMemoryStore", "store"]


