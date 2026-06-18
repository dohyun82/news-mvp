"""
Purpose: JSON 파일 기반 키워드 저장소 (SSOT - Single Source of Truth)

Why: 환경변수 대신 JSON 파일에 키워드를 저장하여 서버 재시작 시에도 설정이
유지되도록 합니다.

How:
- 프로젝트 루트의 data/keywords.json 파일에 키워드 저장
- 파일이 없거나 손상된 경우 기본값 반환
- 파일 쓰기 시 에러 처리 포함

Note: 카테고리 분류는 검토 화면에서 수동으로 하므로, 키워드는 카테고리 구분
없이 단일 수집용 풀(query_keywords)로만 관리한다.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Optional

# 프로젝트 루트 디렉토리 경로 (modules/ 폴더의 부모 디렉토리)
_PROJECT_ROOT = Path(__file__).parent.parent
# 키워드 저장 파일 경로
_KEYWORDS_FILE = _PROJECT_ROOT / "data" / "keywords.json"

# 기본값 정의
_DEFAULT_DATA = {
    "query_keywords": "",  # 뉴스 수집용 키워드 (쉼표 구분 문자열)
    "max_articles": 30,  # 최대 수집 개수
    "max_age_hours": 24,  # 최대 기사 나이 (시간)
}

logger = logging.getLogger("keyword_store")


def _ensure_data_directory() -> None:
    """data 디렉토리가 없으면 생성합니다."""
    _KEYWORDS_FILE.parent.mkdir(parents=True, exist_ok=True)


def _load_keywords() -> Dict:
    """JSON 파일에서 키워드 데이터를 로드합니다. 없거나 손상 시 기본값 반환."""
    if not _KEYWORDS_FILE.exists():
        logger.info("Keywords file not found, using defaults: %s", _KEYWORDS_FILE)
        return _DEFAULT_DATA.copy()

    try:
        with open(_KEYWORDS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # 기본값과 병합하여 누락된 키가 있으면 기본값으로 채움
        merged = _DEFAULT_DATA.copy()
        merged.update(data)
        return merged
    except (json.JSONDecodeError, IOError) as e:
        logger.error("Failed to load keywords file: %s, using defaults", e)
        return _DEFAULT_DATA.copy()


def _save_keywords(data: Dict) -> bool:
    """키워드 데이터를 JSON 파일에 저장합니다."""
    try:
        _ensure_data_directory()
        with open(_KEYWORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("Keywords saved successfully to %s", _KEYWORDS_FILE)
        return True
    except IOError as e:
        logger.error("Failed to save keywords file: %s", e)
        return False


# Getter 메서드들

def get_query_keywords() -> str:
    """뉴스 수집용 키워드(쉼표 구분 문자열)를 반환합니다."""
    return _load_keywords().get("query_keywords", "")


def get_max_articles() -> int:
    """최대 수집 개수를 반환합니다 (기본값: 30)."""
    return _load_keywords().get("max_articles", 30)


def get_max_age_hours() -> int:
    """최대 기사 나이(시간)를 반환합니다 (기본값: 24)."""
    return _load_keywords().get("max_age_hours", 24)


# Setter 메서드들

def update_query_keywords(keywords: str) -> bool:
    """뉴스 수집용 키워드를 업데이트합니다."""
    data = _load_keywords()
    data["query_keywords"] = keywords
    return _save_keywords(data)


def update_max_articles(max_articles: int) -> bool:
    """최대 수집 개수를 업데이트합니다."""
    data = _load_keywords()
    data["max_articles"] = max_articles
    return _save_keywords(data)


def update_max_age_hours(max_age_hours: int) -> bool:
    """최대 기사 나이(시간)를 업데이트합니다."""
    data = _load_keywords()
    data["max_age_hours"] = max_age_hours
    return _save_keywords(data)


def update_all(
    query_keywords: Optional[str] = None,
    max_articles: Optional[int] = None,
    max_age_hours: Optional[int] = None,
) -> bool:
    """여러 설정을 한 번에 업데이트합니다 (None이 아닌 값만)."""
    data = _load_keywords()

    if query_keywords is not None:
        data["query_keywords"] = query_keywords
    if max_articles is not None:
        data["max_articles"] = max_articles
    if max_age_hours is not None:
        data["max_age_hours"] = max_age_hours

    return _save_keywords(data)


__all__ = [
    "get_query_keywords",
    "get_max_articles",
    "get_max_age_hours",
    "update_query_keywords",
    "update_max_articles",
    "update_max_age_hours",
    "update_all",
]
