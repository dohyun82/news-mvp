"""
Purpose: Data models for news clipping application.

Why: Define the Article data structure and in-memory storage for the review workflow.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Article:
    """News article data model.
    
    Attributes:
        title: Article title
        url: Article URL (unique identifier)
        category: Category (그룹사, 업계, 참고, 읽을거리)
        selected: Whether the article is selected for Slack delivery
        summary: AI-generated summary
        description: Article description from Naver API
        pub_date: Publication date from Naver API
        original_category: Original category (for restoration when deselected)
    """
    title: str
    url: str
    category: str
    selected: bool = False
    summary: str = ""
    description: str = ""  # 네이버 API에서 제공하는 기사 요약 정보
    pub_date: str = ""  # 네이버 API에서 제공하는 발행일 (나중에 사용할 수 있도록 저장)
    original_category: str = ""  # 원본 카테고리 (선택 해제 시 복원용)


class InMemoryStore:
    """In-memory storage for news articles.
    
    This is a temporary storage solution for MVP. Can be replaced with
    database-backed storage later.
    """
    
    def __init__(self) -> None:
        self._articles: List[Article] = []

    # CRUD-ish operations
    def set_articles(self, articles: List[Dict[str, str]]) -> None:
        """Set articles from dictionary list."""
        self._articles = [
            Article(
                title=a.get("title", ""),
                url=a.get("url", ""),
                category=a.get("category", "읽을거리"),
                description=a.get("description", ""),  # 네이버 API description 저장
                pub_date=a.get("pub_date", ""),  # 네이버 API 발행일 저장
                original_category=a.get("category", "읽을거리"),  # 원본 카테고리 초기화
            )
            for a in articles
        ]

    def list_articles(self) -> List[Dict[str, str]]:
        """List all articles as dictionaries."""
        return [
            {
                "title": a.title,
                "url": a.url,
                "category": a.category,
                "selected": a.selected,
                "summary": a.summary,
                "description": a.description,  # 네이버 API description 포함
                "pub_date": a.pub_date,  # 네이버 API 발행일 포함
                "original_category": a.original_category,  # 원본 카테고리 포함
            }
            for a in self._articles
        ]

    def delete_by_url(self, url: str) -> bool:
        """Delete an article by URL."""
        before = len(self._articles)
        self._articles = [a for a in self._articles if a.url != url]
        return len(self._articles) != before

    def set_selected(self, url: str, selected: bool) -> bool:
        """Set selection status for an article."""
        for a in self._articles:
            if a.url == url:
                a.selected = selected
                # 선택 해제 시 원본 카테고리로 복원
                if not selected:
                    a.category = a.original_category
                return True
        return False

    def set_category(self, url: str, category: str) -> bool:
        """Update category for an article. original_category is preserved."""
        for a in self._articles:
            if a.url == url:
                a.category = category
                return True
        return False

    def set_summary(self, url: str, summary: str) -> bool:
        """Set summary for an article."""
        for a in self._articles:
            if a.url == url:
                a.summary = summary
                return True
        return False

    def get_selected(self) -> List[Dict[str, str]]:
        """Get all selected articles as dictionaries."""
        return [
            {
                "title": a.title,
                "url": a.url,
                "category": a.category,
                "summary": a.summary,
                "description": a.description,
                "pub_date": a.pub_date,
            }
            for a in self._articles
            if a.selected
        ]

    def get_article_by_url(self, url: str) -> Optional[Article]:
        """Get an article by URL. Returns None if not found."""
        for a in self._articles:
            if a.url == url:
                return a
        return None


# Global store instance
store = InMemoryStore()

__all__ = ["Article", "InMemoryStore", "store"]
