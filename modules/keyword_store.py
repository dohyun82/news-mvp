"""
Purpose: JSON 파일 기반 키워드 저장소 (SSOT - Single Source of Truth)

Why: 환경변수 대신 JSON 파일에 키워드를 저장하여 서버 재시작 시에도 설정이 유지되도록 합니다.
SSOT 원칙에 따라 모든 키워드는 이 모듈을 통해서만 접근합니다.

How: 
- 프로젝트 루트의 data/keywords.json 파일에 키워드 저장
- 파일이 없거나 손상된 경우 기본값 반환
- 파일 쓰기 시 에러 처리 포함
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

# 프로젝트 루트 디렉토리 경로 (modules/ 폴더의 부모 디렉토리)
_PROJECT_ROOT = Path(__file__).parent.parent
# 키워드 저장 파일 경로
_KEYWORDS_FILE = _PROJECT_ROOT / "data" / "keywords.json"

# 기본값 정의
_DEFAULT_DATA = {
    "query_keywords": "",  # 뉴스 수집용 키워드 (쉼표 구분 문자열)
    "category_keywords": {  # 카테고리별 키워드 딕셔너리
        "그룹사": [],
        "업계": [],
        "참고": [],
    },
    "max_articles": 30,  # 최대 수집 개수
    "max_age_hours": 24,  # 최대 기사 나이 (시간)
}

logger = logging.getLogger("keyword_store")


def _ensure_data_directory() -> None:
    """data 디렉토리가 없으면 생성합니다.
    
    동작 원리:
    1. _KEYWORDS_FILE의 부모 디렉토리 (data/) 경로 확인
    2. 디렉토리가 없으면 생성 (parents=True: 상위 디렉토리도 함께 생성)
    3. exist_ok=True: 이미 존재해도 에러 발생하지 않음
    """
    _KEYWORDS_FILE.parent.mkdir(parents=True, exist_ok=True)


def _load_keywords() -> Dict:
    """JSON 파일에서 키워드 데이터를 로드합니다.
    
    Returns:
        키워드 데이터 딕셔너리. 파일이 없거나 손상된 경우 기본값 반환.
        
    동작 원리:
    1. 파일이 존재하는지 확인
    2. 존재하면 JSON 파일 읽기
    3. 파일이 없거나 JSON 파싱 실패 시 기본값 반환
    4. 로드된 데이터와 기본값을 병합하여 누락된 키가 있으면 기본값으로 채움
    """
    if not _KEYWORDS_FILE.exists():
        logger.info("Keywords file not found, using defaults: %s", _KEYWORDS_FILE)
        return _DEFAULT_DATA.copy()
    
    try:
        with open(_KEYWORDS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 기본값과 병합하여 누락된 키가 있으면 기본값으로 채움
        merged = _DEFAULT_DATA.copy()
        merged.update(data)
        
        # category_keywords도 병합 (각 카테고리별로)
        if "category_keywords" in data:
            merged["category_keywords"] = _DEFAULT_DATA["category_keywords"].copy()
            merged["category_keywords"].update(data.get("category_keywords", {}))
        
        return merged
    except (json.JSONDecodeError, IOError) as e:
        logger.error("Failed to load keywords file: %s, using defaults", e)
        return _DEFAULT_DATA.copy()


def _save_keywords(data: Dict) -> bool:
    """키워드 데이터를 JSON 파일에 저장합니다.
    
    Args:
        data: 저장할 키워드 데이터 딕셔너리
        
    Returns:
        저장 성공 여부 (True/False)
        
    동작 원리:
    1. data 디렉토리 존재 확인 및 생성
    2. JSON 파일에 데이터 쓰기 (indent=2: 가독성을 위한 들여쓰기)
    3. 파일 쓰기 실패 시 에러 로깅 및 False 반환
    """
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
    """뉴스 수집용 키워드를 반환합니다.
    
    Returns:
        쉼표로 구분된 키워드 문자열 (예: "키워드1,키워드2")
    """
    data = _load_keywords()
    return data.get("query_keywords", "")


def get_category_keywords() -> Dict[str, List[str]]:
    """카테고리별 키워드를 반환합니다.
    
    Returns:
        카테고리별 키워드 딕셔너리 (예: {"그룹사": ["키워드1"], "업계": ["키워드2"]})
    """
    data = _load_keywords()
    return data.get("category_keywords", _DEFAULT_DATA["category_keywords"].copy())


def get_max_articles() -> int:
    """최대 수집 개수를 반환합니다.
    
    Returns:
        최대 수집 개수 (기본값: 30)
    """
    data = _load_keywords()
    return data.get("max_articles", 30)


def get_max_age_hours() -> int:
    """최대 기사 나이(시간)를 반환합니다.
    
    Returns:
        최대 기사 나이 (기본값: 24)
    """
    data = _load_keywords()
    return data.get("max_age_hours", 24)


# Setter 메서드들

def update_query_keywords(keywords: str) -> bool:
    """뉴스 수집용 키워드를 업데이트합니다.
    
    Args:
        keywords: 쉼표로 구분된 키워드 문자열
        
    Returns:
        저장 성공 여부
        
    동작 원리:
    1. 현재 데이터 로드
    2. query_keywords 필드만 업데이트
    3. 파일에 저장
    """
    data = _load_keywords()
    data["query_keywords"] = keywords
    return _save_keywords(data)


def update_category_keywords(category_keywords: Dict[str, List[str]]) -> bool:
    """카테고리별 키워드를 업데이트합니다.
    
    Args:
        category_keywords: 카테고리별 키워드 딕셔너리
        
    Returns:
        저장 성공 여부
        
    동작 원리:
    1. 현재 데이터 로드
    2. category_keywords 필드만 업데이트
    3. 파일에 저장
    """
    data = _load_keywords()
    data["category_keywords"] = category_keywords
    return _save_keywords(data)


def update_max_articles(max_articles: int) -> bool:
    """최대 수집 개수를 업데이트합니다.
    
    Args:
        max_articles: 최대 수집 개수 (양수)
        
    Returns:
        저장 성공 여부
    """
    data = _load_keywords()
    data["max_articles"] = max_articles
    return _save_keywords(data)


def update_max_age_hours(max_age_hours: int) -> bool:
    """최대 기사 나이(시간)를 업데이트합니다.
    
    Args:
        max_age_hours: 최대 기사 나이 (0 이상)
        
    Returns:
        저장 성공 여부
    """
    data = _load_keywords()
    data["max_age_hours"] = max_age_hours
    return _save_keywords(data)


def update_all(
    query_keywords: Optional[str] = None,
    category_keywords: Optional[Dict[str, List[str]]] = None,
    max_articles: Optional[int] = None,
    max_age_hours: Optional[int] = None,
) -> bool:
    """여러 설정을 한 번에 업데이트합니다.
    
    Args:
        query_keywords: 뉴스 수집용 키워드 (None이면 업데이트 안 함)
        category_keywords: 카테고리별 키워드 (None이면 업데이트 안 함)
        max_articles: 최대 수집 개수 (None이면 업데이트 안 함)
        max_age_hours: 최대 기사 나이 (None이면 업데이트 안 함)
        
    Returns:
        저장 성공 여부
        
    동작 원리:
    1. 현재 데이터 로드
    2. None이 아닌 파라미터만 업데이트
    3. 파일에 저장 (한 번만)
    """
    data = _load_keywords()
    
    if query_keywords is not None:
        data["query_keywords"] = query_keywords
    if category_keywords is not None:
        data["category_keywords"] = category_keywords
    if max_articles is not None:
        data["max_articles"] = max_articles
    if max_age_hours is not None:
        data["max_age_hours"] = max_age_hours
    
    return _save_keywords(data)


__all__ = [
    "get_query_keywords",
    "get_category_keywords",
    "get_max_articles",
    "get_max_age_hours",
    "update_query_keywords",
    "update_category_keywords",
    "update_max_articles",
    "update_max_age_hours",
    "update_all",
]

