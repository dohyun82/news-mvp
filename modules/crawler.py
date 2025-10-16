from __future__ import annotations

from typing import Dict, List
import json
import urllib.parse
import urllib.request
import time
import logging

from .config import get_default_keywords_by_category, RealDataConfig
from .curation import curate


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
        title = it.get("title", "").replace("<b>", "").replace("</b>", "")
        url = it.get("originallink") or it.get("link") or ""
        if title and url:
            results.append({"title": title, "url": url})
    return results


def crawl_naver_news(keywords: List[str]) -> List[Dict[str, str]]:
    """
    Collect news by keywords. MVP phase uses stubbed data; replace with
    real crawling (requests/feeds) later.

    Returns curated list with categories and basic dedup/filters applied.
    """

    logger = logging.getLogger("crawler.naver")
    logger.info("crawl_naver_news started (realdata toggle: %s)", cfg.enabled)

    cfg = RealDataConfig()
    raw_articles: List[Dict[str, str]] = []
    if cfg.enabled and cfg.client_id and cfg.client_secret:
        # 실데이터 경로: 키워드 목록(ENV 또는 인자) 기준으로 호출
        kw_list = [k.strip() for k in (cfg.query_keywords or ",".join(keywords)).split(",") if k.strip()]
        remaining = cfg.max_articles
        started = time.perf_counter()
        failures = 0
        for kw in kw_list:
            if remaining <= 0:
                break
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
                except Exception as e:
                    attempts += 1
                    if attempts >= 3:
                        failures += 1
                        logger.error("naver api fetch failed for kw='%s': %s", kw, e)
                finally:
                    time.sleep(max(0.0, cfg.delay_ms / 1000.0))
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        logger.info("naver fetch done: total_raw=%d failures=%d elapsed_ms=%d", len(raw_articles), failures, elapsed_ms)
    else:
        # 스텁 데이터 (기존 동작)
        raw_articles = [
            {"title": "현대백화점그룹, 식권대장과 협력 강화", "url": "http://example.com/a"},
            {"title": "기업 복지 포인트, 이커머스와 연계 확대", "url": "http://example.com/b"},
            {"title": "[광고] 최고의 프로모션 소식", "url": "http://example.com/c"},
            {"title": "현대백화점그룹, 식권대장과 협력 강화", "url": "http://example.com/a-dup"},
            {"title": "밀키트 수요 증가와 푸드테크 트렌드", "url": "http://example.com/d"},
        ]

    keywords_by_category = get_default_keywords_by_category()
    result = curate(raw_articles, keywords_by_category)
    return result


