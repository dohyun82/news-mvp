from __future__ import annotations

from typing import Dict, List, Optional
import json
import html
import urllib.parse
import urllib.request
import time
import logging
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

from .config import RealDataConfig
from .curation import curate
from . import keyword_store


def _fetch_naver_news_api(query: str, *, display: int, start: int, sort: str, timeout: int,
                          client_id: str, client_secret: str) -> List[Dict[str, str]]:
    base = "https://openapi.naver.com/v1/search/news.json"
    qs = urllib.parse.urlencode({
        "query": query,
        "display": display,
        "start": start,
        "sort": sort,
    })
    req = urllib.request.Request(f"{base}?{qs}")
    req.add_header("X-Naver-Client-Id", client_id)
    req.add_header("X-Naver-Client-Secret", client_secret)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.load(resp)
    items = data.get("items", [])
    results: List[Dict[str, str]] = []
    for it in items:
        # HTML 태그 제거 및 HTML 엔티티 디코딩
        title = it.get("title", "").replace("<b>", "").replace("</b>", "")
        title = html.unescape(title)  # HTML 엔티티 디코딩 (&quot; -> ")
        url = it.get("originallink") or it.get("link") or ""
        # 네이버 API에서 제공하는 description (기사 요약 정보)
        description = it.get("description", "").replace("<b>", "").replace("</b>", "").strip()
        description = html.unescape(description)  # HTML 엔티티 디코딩
        # 네이버 API에서 제공하는 발행일 (나중에 사용할 수 있도록 저장)
        pub_date = it.get("pubDate", "").strip()
        if title and url:
            article = {"title": title, "url": url}
            if description:
                article["description"] = description
            if pub_date:
                article["pub_date"] = pub_date
            results.append(article)
    return results


def _filter_by_age(articles: List[Dict[str, str]], max_age_hours: Optional[int]) -> List[Dict[str, str]]:
    """발행 시간을 기준으로 기사를 필터링합니다.
    
    Args:
        articles: 필터링할 기사 리스트
        max_age_hours: 최대 기사 나이 (시간). None이거나 0이면 필터링하지 않음.
    
    Returns:
        필터링된 기사 리스트 (pub_date가 없거나 설정된 시간 이전의 기사는 제외)
    """
    if not max_age_hours or max_age_hours <= 0:
        return articles
    
    # 현재 시간을 UTC 기준으로 가져오기 (타임존 문제 방지)
    from datetime import timezone
    now = datetime.now(timezone.utc)
    cutoff_time = now - timedelta(hours=max_age_hours)
    filtered: List[Dict[str, str]] = []
    
    for article in articles:
        pub_date_str = article.get("pub_date", "").strip()
        if not pub_date_str:
            # pub_date가 없는 기사는 제외
            continue
        
        try:
            # RFC 822 형식 파싱 (예: "Thu, 13 Nov 2025 16:56:00 +0900")
            pub_datetime = parsedate_to_datetime(pub_date_str)
            # 타임존 정보가 없으면 UTC로 가정
            if pub_datetime.tzinfo is None:
                pub_datetime = pub_datetime.replace(tzinfo=timezone.utc)
            else:
                # UTC로 변환하여 비교
                pub_datetime = pub_datetime.astimezone(timezone.utc)
            
            # 설정된 시간 이후에 발행된 기사만 포함
            if pub_datetime >= cutoff_time:
                filtered.append(article)
        except (ValueError, TypeError) as e:
            # 날짜 파싱 실패 시 해당 기사는 제외
            logging.getLogger("crawler.naver").warning("Failed to parse pub_date '%s': %s", pub_date_str, e)
            continue
    
    return filtered


def crawl_naver_news(keywords: List[str] = None, user_keywords: str = None, user_max_articles: int = None, user_category_keywords: Dict[str, List[str]] = None, user_max_age_hours: int = None) -> List[Dict[str, str]]:
    """
    Collect news by keywords. MVP phase uses stubbed data; replace with
    real crawling (requests/feeds) later.

    Args:
        keywords: 기존 키워드 리스트 (하위 호환성 유지)
        user_keywords: 사용자가 설정한 키워드 (쉼표 구분 문자열, 우선순위 높음)
        user_max_articles: 사용자가 설정한 최대 수집 개수 (우선순위 높음)
        user_category_keywords: 사용자가 설정한 카테고리별 키워드 딕셔너리 (우선순위 높음)
        user_max_age_hours: 사용자가 설정한 최대 기사 나이 (시간, 우선순위 높음)

    Returns curated list with categories and basic dedup/filters applied.
    """

    logger = logging.getLogger("crawler.naver")
    cfg = RealDataConfig()
    logger.info("crawl_naver_news started (realdata toggle: %s)", cfg.enabled)
    raw_articles: List[Dict[str, str]] = []
    if cfg.enabled and cfg.client_id and cfg.client_secret:
        # 키워드 우선순위: 사용자 설정 > keyword_store > 함수 인자
        if user_keywords:
            kw_list = [k.strip() for k in user_keywords.split(",") if k.strip()]
        else:
            # keyword_store에서 키워드 가져오기
            stored_keywords = keyword_store.get_query_keywords()
            if stored_keywords:
                kw_list = [k.strip() for k in stored_keywords.split(",") if k.strip()]
            elif keywords:
                kw_list = [k.strip() for k in keywords if k.strip()]
            else:
                kw_list = []
        
        # 최대 수집 개수: 사용자 설정 > keyword_store
        # 각 키워드마다 이 개수만큼 수집 (전체 합계가 아님)
        if user_max_articles is not None:
            max_per_keyword = user_max_articles
        else:
            max_per_keyword = keyword_store.get_max_articles()
        started = time.perf_counter()
        failures = 0
        for kw in kw_list:
            # 각 키워드마다 독립적으로 최대 수집 개수만큼 수집
            remaining = max_per_keyword
            while remaining > 0:
                batch = min(100, remaining)
                # 간단 재시도(최대 2회) + 호출 간 딜레이
                attempts = 0
                success = False
                while attempts < 3 and not success:
                    try:
                        items = _fetch_naver_news_api(
                            kw,
                            display=batch,
                            start=1,
                            sort=cfg.sort,
                            timeout=max(1, cfg.timeout_ms // 1000),
                            client_id=cfg.client_id,
                            client_secret=cfg.client_secret,
                        )
                        raw_articles.extend(items)
                        remaining -= len(items)
                        success = True
                        logger.info("fetched %d items for kw='%s' (remaining=%d)", len(items), kw, remaining)
                        # API에서 반환된 개수가 batch보다 적으면 더 이상 수집할 수 없음
                        if len(items) < batch:
                            remaining = 0
                    except Exception as e:
                        attempts += 1
                        if attempts >= 3:
                            failures += 1
                            logger.error("naver api fetch failed for kw='%s': %s", kw, e)
                            remaining = 0  # 실패 시 해당 키워드 수집 중단
                    finally:
                        time.sleep(max(0.0, cfg.delay_ms / 1000.0))
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        logger.info("naver fetch done: total_raw=%d failures=%d elapsed_ms=%d", len(raw_articles), failures, elapsed_ms)
    else:
        # 스텁 데이터 (기존 동작)
        raw_articles = [
            {
                "title": "현대백화점그룹, 식권대장과 협력 강화",
                "url": "http://example.com/a",
                "description": "현대백화점그룹이 식권대장과의 협력을 강화하며 기업 복지 서비스 확대를 추진한다고 발표했다.",
                "pub_date": "Thu, 13 Nov 2025 16:56:00 +0900",
            },
            {
                "title": "기업 복지 포인트, 이커머스와 연계 확대",
                "url": "http://example.com/b",
                "description": "기업 복지 포인트가 주요 이커머스 플랫폼과 연계를 확대하여 직원들의 복지 혜택을 늘린다.",
                "pub_date": "Thu, 13 Nov 2025 14:30:00 +0900",
            },
            {
                "title": "[광고] 최고의 프로모션 소식",
                "url": "http://example.com/c",
            },
            {
                "title": "현대백화점그룹, 식권대장과 협력 강화",
                "url": "http://example.com/a-dup",
                "description": "현대백화점그룹이 식권대장과의 협력을 강화하며 기업 복지 서비스 확대를 추진한다고 발표했다.",
                "pub_date": "Thu, 13 Nov 2025 16:56:00 +0900",
            },
            {
                "title": "밀키트 수요 증가와 푸드테크 트렌드",
                "url": "http://example.com/d",
                "description": "밀키트 시장이 지속적으로 성장하며 푸드테크 산업의 새로운 트렌드로 주목받고 있다.",
                "pub_date": "Thu, 13 Nov 2025 12:15:00 +0900",
            },
        ]

    # 최대 기사 나이 필터링: 사용자 설정 > keyword_store
    if user_max_age_hours is not None:
        max_age_hours = user_max_age_hours
    else:
        max_age_hours = keyword_store.get_max_age_hours()
    
    # 시간 기반 필터링 적용
    raw_articles = _filter_by_age(raw_articles, max_age_hours)
    logger.info("after age filtering: %d articles", len(raw_articles))

    # 카테고리별 키워드: 사용자 설정 > keyword_store
    if user_category_keywords is not None:
        keywords_by_category = user_category_keywords
    else:
        keywords_by_category = keyword_store.get_category_keywords()
    
    result = curate(raw_articles, keywords_by_category)
    return result


