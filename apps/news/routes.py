"""
Purpose: Routes for news clipping application.

Why: Centralize all news-related routes in the news Blueprint.

How: Define routes with /news prefix and handle all news clipping operations.
"""

from __future__ import annotations

import logging
from flask import jsonify, render_template, request

from . import news_bp
from .models import store
from .services import collect_news, get_keyword_settings, save_keyword_settings
from shared.ai.openai_client import get_summary_from_openai
from shared.integrations.slack import send_message_to_slack
from shared.news.article_content_extractor import extract_article_content


# News collection API
@news_bp.route('/api/collect', methods=['POST'])
def collect_news_route():
    """뉴스 수집 API.
    
    keyword_store에서 키워드 설정을 읽어와 뉴스를 수집합니다.
    """
    articles = collect_news()
    store.set_articles(articles)
    return jsonify({"count": len(articles)})


@news_bp.route('/api/summarize', methods=['POST'])
def summarize_news_route():
    """뉴스 요약 API."""
    data = request.get_json(silent=True) or {}
    url = data.get("url")
    if not url:
        return jsonify({"error": "url is required"}), 400
    
    # store에서 기사 정보 가져오기 (제목을 함께 전달하기 위해)
    article = store.get_article_by_url(url)
    title = article.title if article else None
    description = (article.description or "").strip() if article else ""

    extract_result = extract_article_content(url)
    article_text = extract_result.text if extract_result.status == "ok" else ""
    input_source = "article_text" if article_text else ("description" if description else "title")
    
    # OpenAI API 호출 (본문 우선, 실패 시 description으로 fallback)
    summary = get_summary_from_openai(
        url,
        title=title,
        description=description or None,
        article_text=article_text or None,
    )

    summary_error = ""
    if "요약 실패 (" in summary:
        summary_error = summary
        if description:
            summary = description
            input_source = "description"
        else:
            summary = ""
            input_source = "none" if not title else "title"

    store.set_summary(url, summary)
    return jsonify(
        {
            "url": url,
            "summary": summary,
            "input_source": input_source,
            "extract_status": extract_result.status,
            "extract_source": extract_result.source,
            "summary_error": summary_error,
        }
    )


@news_bp.route('/api/send-slack', methods=['POST'])
def send_slack_route():
    """슬랙 발송 API."""
    selected = store.get_selected()
    success, message = send_message_to_slack(selected)
    return jsonify({"success": success, "message": message})


# Review workflow APIs
@news_bp.route('/api/review/list', methods=['GET'])
def review_list_route():
    """뉴스 목록 조회 API."""
    return jsonify(store.list_articles())


@news_bp.route('/api/review/delete', methods=['POST'])
def review_delete_route():
    """뉴스 삭제 API."""
    data = request.get_json(silent=True) or {}
    url = data.get("url")
    if not url:
        return jsonify({"error": "url is required"}), 400
    ok = store.delete_by_url(url)
    return jsonify({"deleted": ok})


@news_bp.route('/api/review/select', methods=['POST'])
def review_select_route():
    """뉴스 선택/해제 API."""
    data = request.get_json(silent=True) or {}
    url = data.get("url")
    selected = bool(data.get("selected", True))
    if not url:
        return jsonify({"error": "url is required"}), 400
    ok = store.set_selected(url, selected)
    return jsonify({"updated": ok})


@news_bp.route('/api/review/category', methods=['POST'])
def review_category_route():
    """뉴스 카테고리 변경 API."""
    try:
        data = request.get_json(silent=True) or {}
        url = data.get("url")
        category = data.get("category")
        
        if not url:
            return jsonify({"error": "url is required"}), 400
        if not category:
            return jsonify({"error": "category is required"}), 400
        
        # 유효한 카테고리인지 확인
        valid_categories = ["그룹사", "업계", "참고", "읽을거리"]
        if category not in valid_categories:
            return jsonify({"error": f"invalid category: {category}. Must be one of {valid_categories}"}), 400
        
        # Article 존재 여부 확인
        article = store.get_article_by_url(url)
        if not article:
            return jsonify({"error": "article not found"}), 404
        
        ok = store.set_category(url, category)
        if not ok:
            return jsonify({"error": "failed to update category"}), 500
        
        return jsonify({"updated": ok})
    except Exception as e:
        logging.getLogger("errors").exception("Error in review_category: %s", e)
        return jsonify({"error": {"type": e.__class__.__name__, "message": str(e)}}), 500


# Settings APIs
@news_bp.route('/api/settings/initial-values', methods=['GET'])
def settings_initial_values_route():
    """keyword_store에서 초기값을 읽어서 반환합니다.
    
    로컬 스토리지에 값이 없을 때만 사용됩니다.
    """
    settings = get_keyword_settings()
    return jsonify({
        "keywords": settings["keywords"],
        "max_articles": settings["max_articles"],
        "category_keywords": settings["category_keywords"],
        "max_age_hours": settings["max_age_hours"],
    })


@news_bp.route('/api/settings/save', methods=['POST'])
def settings_save_route():
    """사용자 설정을 keyword_store에 저장합니다.
    
    요청 본문:
    - keywords: 쉼표로 구분된 키워드 문자열
    - max_articles: 최대 수집 뉴스 개수 (정수)
    - category_keywords: 카테고리별 키워드 딕셔너리 {"그룹사": ["키워드1", ...], "업계": [...], "참고": [...]}
    - max_age_hours: 최대 기사 나이 (시간, 정수, 0 이상)
    """
    try:
        data = request.get_json(silent=True) or {}
        keywords = data.get("keywords")
        max_articles = data.get("max_articles")
        category_keywords = data.get("category_keywords")
        max_age_hours = data.get("max_age_hours")
        
        # 검증
        if keywords is not None:
            if not isinstance(keywords, str):
                return jsonify({"error": "keywords must be a string"}), 400
        
        if max_articles is not None:
            try:
                max_articles = int(max_articles)
                if max_articles <= 0:
                    return jsonify({"error": "max_articles must be a positive integer"}), 400
            except (ValueError, TypeError):
                return jsonify({"error": "max_articles must be an integer"}), 400
        
        if category_keywords is not None:
            if not isinstance(category_keywords, dict):
                return jsonify({"error": "category_keywords must be a dictionary"}), 400
            # 유효한 카테고리인지 확인
            valid_categories = ["그룹사", "업계", "참고"]
            for category in category_keywords.keys():
                if category not in valid_categories:
                    return jsonify({"error": f"invalid category: {category}. Must be one of {valid_categories}"}), 400
            # 각 카테고리의 값이 리스트인지 확인
            for category, keywords_list in category_keywords.items():
                if not isinstance(keywords_list, list):
                    return jsonify({"error": f"category_keywords[{category}] must be a list"}), 400
                # 리스트 내 모든 항목이 문자열인지 확인
                if not all(isinstance(kw, str) for kw in keywords_list):
                    return jsonify({"error": f"category_keywords[{category}] must contain only strings"}), 400
        
        if max_age_hours is not None:
            try:
                max_age_hours = int(max_age_hours)
                if max_age_hours < 0:
                    return jsonify({"error": "max_age_hours must be 0 or greater"}), 400
            except (ValueError, TypeError):
                return jsonify({"error": "max_age_hours must be an integer"}), 400
        
        # 저장
        success = save_keyword_settings(
            keywords=keywords,
            max_articles=max_articles,
            category_keywords=category_keywords,
            max_age_hours=max_age_hours
        )
        
        if not success:
            return jsonify({"error": "failed to save settings"}), 500
        
        return jsonify({"saved": True})
    except Exception as e:
        logging.getLogger("errors").exception("Error in settings_save: %s", e)
        return jsonify({"error": {"type": e.__class__.__name__, "message": str(e)}}), 500


@news_bp.route('/api/settings/get', methods=['GET'])
def settings_get_route():
    """keyword_store에서 저장된 설정을 반환합니다.
    
    모든 설정은 keyword_store(JSON 파일)에서 읽어옵니다.
    """
    settings = get_keyword_settings()
    return jsonify({
        "keywords": settings["keywords"],
        "max_articles": settings["max_articles"],
        "category_keywords": settings["category_keywords"],
        "max_age_hours": settings["max_age_hours"],
    })


# Page routes
@news_bp.route('/review')
def review_page():
    """뉴스 클리핑 검토 페이지."""
    return render_template('review.html', current_page='review')


@news_bp.route('/settings')
def settings_page():
    """뉴스 클리핑 설정 페이지."""
    return render_template('settings.html')
