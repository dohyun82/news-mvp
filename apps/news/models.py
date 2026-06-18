"""
Purpose: Data models and file-backed storage for the news clipping application.

Why: Define the Article data structure and persist the review workflow state so
that collected articles, selections, and summaries survive a server restart.

How: Keep state in memory for fast access and write changes to a JSON file
(best-effort). The persistence path can be overridden via ARTICLES_STORE_PATH
(useful for tests).
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional

from core.categories import UNCATEGORIZED

logger = logging.getLogger("news.store")

# 수집/검토 상태를 보존할 JSON 파일 경로 (환경변수로 재정의 가능)
_DEFAULT_STORE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "articles.json"


@dataclass
class Article:
    """News article data model.

    Attributes:
        title: Article title
        url: Article URL (unique identifier)
        category: Category (core.categories.NEWS_CATEGORIES 중 하나 또는 미분류)
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
    pub_date: str = ""  # 네이버 API에서 제공하는 발행일
    original_category: str = ""  # 원본 카테고리 (선택 해제 시 복원용)


class InMemoryStore:
    """File-backed storage for news articles.

    상태를 메모리에 유지하되 변경 시 JSON 파일에 저장하여 서버 재시작 후에도
    수집/검토 상태가 보존되도록 한다. 저장/로드는 best-effort이며 실패해도
    메모리 동작에는 영향을 주지 않는다.
    """

    def __init__(self, persist_path: Optional[str] = None) -> None:
        self._persist_path = Path(
            persist_path or os.getenv("ARTICLES_STORE_PATH", str(_DEFAULT_STORE_PATH))
        )
        self._articles: List[Article] = []
        self._load_from_disk()

    # 영속성 헬퍼
    def _load_from_disk(self) -> None:
        """시작 시 저장된 기사 상태를 로드한다. 파일이 없거나 손상되면 빈 상태."""
        if not self._persist_path.exists():
            return
        try:
            with open(self._persist_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._articles = [Article(**item) for item in data]
            logger.info("기사 %d건 로드: %s", len(self._articles), self._persist_path)
        except (json.JSONDecodeError, IOError, TypeError) as e:
            logger.warning("기사 저장 파일 로드 실패(%s) — 빈 상태로 시작", e)
            self._articles = []

    def _save_to_disk(self) -> None:
        """현재 기사 상태를 JSON 파일에 저장한다(best-effort)."""
        try:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._persist_path, "w", encoding="utf-8") as f:
                json.dump([asdict(a) for a in self._articles], f, ensure_ascii=False, indent=2)
        except IOError as e:
            logger.warning("기사 저장 실패(%s)", e)

    # CRUD-ish operations
    def set_articles(self, articles: List[Dict[str, str]]) -> None:
        """Set articles from dictionary list."""
        self._articles = [
            Article(
                title=a.get("title", ""),
                url=a.get("url", ""),
                category=a.get("category", UNCATEGORIZED),
                description=a.get("description", ""),  # 네이버 API description 저장
                pub_date=a.get("pub_date", ""),  # 네이버 API 발행일 저장
                original_category=a.get("category", UNCATEGORIZED),  # 원본 카테고리 초기화
            )
            for a in articles
        ]
        self._save_to_disk()

    def list_articles(self) -> List[Dict[str, str]]:
        """List all articles as dictionaries."""
        return [
            {
                "title": a.title,
                "url": a.url,
                "category": a.category,
                "selected": a.selected,
                "summary": a.summary,
                "description": a.description,
                "pub_date": a.pub_date,
                "original_category": a.original_category,
            }
            for a in self._articles
        ]

    def delete_by_url(self, url: str) -> bool:
        """Delete an article by URL."""
        before = len(self._articles)
        self._articles = [a for a in self._articles if a.url != url]
        changed = len(self._articles) != before
        if changed:
            self._save_to_disk()
        return changed

    def set_selected(self, url: str, selected: bool) -> bool:
        """Set selection status for an article."""
        for a in self._articles:
            if a.url == url:
                a.selected = selected
                # 선택 해제 시 원본 카테고리로 복원
                if not selected:
                    a.category = a.original_category
                self._save_to_disk()
                return True
        return False

    def set_category(self, url: str, category: str) -> bool:
        """Update category for an article. original_category is preserved."""
        for a in self._articles:
            if a.url == url:
                a.category = category
                self._save_to_disk()
                return True
        return False

    def set_summary(self, url: str, summary: str) -> bool:
        """Set summary for an article."""
        for a in self._articles:
            if a.url == url:
                a.summary = summary
                self._save_to_disk()
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
