from flask import Flask, jsonify, render_template, request
from modules import crawler, gemini, slack
from modules.store import store
from modules.common import configure_logging, register_http_logging, register_error_handlers
from modules.config import RealDataConfig, get_default_keywords_by_category

app = Flask(__name__)

# 개발 모드: 템플릿 캐시 비활성화 (코드 변경 즉시 반영)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # 정적 파일 캐시 비활성화

# Common logging / error handling
configure_logging()
register_http_logging(app)
register_error_handlers(app)

# 사용자 설정 저장소 (인메모리, 서버 재시작 시 초기화됨)
# 환경 변수는 초기값 제공용으로만 사용
_user_settings = {
    "keywords": None,  # None이면 환경 변수 사용
    "max_articles": None,  # None이면 환경 변수 사용
    "category_keywords": None,  # None이면 기본 키워드 사용
}

@app.route('/api/collect', methods=['POST'])
def collect_news():
    # 저장된 사용자 설정 가져오기
    user_keywords = _user_settings["keywords"]
    user_max_articles = _user_settings["max_articles"]
    user_category_keywords = _user_settings["category_keywords"]
    
    articles = crawler.crawl_naver_news(
        keywords=[],
        user_keywords=user_keywords,
        user_max_articles=user_max_articles,
        user_category_keywords=user_category_keywords
    )
    store.set_articles(articles)
    return jsonify({"count": len(articles)})

@app.route('/api/summarize', methods=['POST'])
def summarize_news():
    data = request.get_json(silent=True) or {}
    url = data.get("url")
    if not url:
        return jsonify({"error": "url is required"}), 400
    
    # store에서 기사 정보 가져오기 (제목을 함께 전달하기 위해)
    article = store.get_article_by_url(url)
    title = article.title if article else None
    
    # Gemini API 호출 (제목이 있으면 함께 전달)
    summary = gemini.get_summary_from_gemini(url, title=title)
    store.set_summary(url, summary)
    return jsonify({"url": url, "summary": summary})

@app.route('/api/send-slack', methods=['POST'])
def send_slack():
    selected = store.get_selected()
    success, message = slack.send_message_to_slack(selected)
    return jsonify({"success": success, "message": message})

# Review workflow APIs
@app.route('/api/review/list', methods=['GET'])
def review_list():
    return jsonify(store.list_articles())

@app.route('/api/review/delete', methods=['POST'])
def review_delete():
    data = request.get_json(silent=True) or {}
    url = data.get("url")
    if not url:
        return jsonify({"error": "url is required"}), 400
    ok = store.delete_by_url(url)
    return jsonify({"deleted": ok})

@app.route('/api/review/select', methods=['POST'])
def review_select():
    data = request.get_json(silent=True) or {}
    url = data.get("url")
    selected = bool(data.get("selected", True))
    if not url:
        return jsonify({"error": "url is required"}), 400
    ok = store.set_selected(url, selected)
    return jsonify({"updated": ok})

@app.route('/api/review/category', methods=['POST'])
def review_category():
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
        import logging
        logging.getLogger("errors").exception("Error in review_category: %s", e)
        return jsonify({"error": {"type": e.__class__.__name__, "message": str(e)}}), 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/review')
def review_page():
    return render_template('review.html')

@app.route('/settings')
def settings_page():
    return render_template('settings.html')

@app.route('/api/settings/initial-values', methods=['GET'])
def settings_initial_values():
    """환경 변수에서 초기값을 읽어서 반환합니다.
    
    로컬 스토리지에 값이 없을 때만 사용됩니다.
    """
    import logging
    logger = logging.getLogger("app")
    
    cfg = RealDataConfig()
    default_category_keywords = get_default_keywords_by_category()
    
    # 디버깅: 환경변수 값 확인
    logger.info("Environment variables check:")
    logger.info("  CATEGORY_GROUP_KEYWORDS: %s", cfg.group_keywords)
    logger.info("  CATEGORY_INDUSTRY_KEYWORDS: %s", cfg.industry_keywords)
    logger.info("  CATEGORY_REFERENCE_KEYWORDS: %s", cfg.reference_keywords)
    logger.info("  Parsed category_keywords: %s", default_category_keywords)
    
    return jsonify({
        "keywords": cfg.query_keywords,
        "max_articles": cfg.max_articles,
        "category_keywords": default_category_keywords,
    })

@app.route('/api/settings/save', methods=['POST'])
def settings_save():
    """사용자 설정을 저장합니다.
    
    요청 본문:
    - keywords: 쉼표로 구분된 키워드 문자열
    - max_articles: 최대 수집 뉴스 개수 (정수)
    - category_keywords: 카테고리별 키워드 딕셔너리 {"그룹사": ["키워드1", ...], "업계": [...], "참고": [...]}
    """
    try:
        data = request.get_json(silent=True) or {}
        keywords = data.get("keywords")
        max_articles = data.get("max_articles")
        category_keywords = data.get("category_keywords")
        
        if keywords is not None:
            if not isinstance(keywords, str):
                return jsonify({"error": "keywords must be a string"}), 400
            _user_settings["keywords"] = keywords
        
        if max_articles is not None:
            try:
                max_articles = int(max_articles)
                if max_articles <= 0:
                    return jsonify({"error": "max_articles must be a positive integer"}), 400
            except (ValueError, TypeError):
                return jsonify({"error": "max_articles must be an integer"}), 400
            _user_settings["max_articles"] = max_articles
        
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
            _user_settings["category_keywords"] = category_keywords
        
        return jsonify({"saved": True})
    except Exception as e:
        import logging
        logging.getLogger("errors").exception("Error in settings_save: %s", e)
        return jsonify({"error": {"type": e.__class__.__name__, "message": str(e)}}), 500

@app.route('/api/settings/get', methods=['GET'])
def settings_get():
    """저장된 사용자 설정을 반환합니다.
    
    저장된 값이 없으면 환경 변수 값 또는 기본값을 반환합니다.
    """
    cfg = RealDataConfig()
    keywords = _user_settings["keywords"] if _user_settings["keywords"] is not None else cfg.query_keywords
    max_articles = _user_settings["max_articles"] if _user_settings["max_articles"] is not None else cfg.max_articles
    category_keywords = _user_settings["category_keywords"] if _user_settings["category_keywords"] is not None else get_default_keywords_by_category()
    
    return jsonify({
        "keywords": keywords,
        "max_articles": max_articles,
        "category_keywords": category_keywords,
    })

if __name__ == '__main__':
    # 개발 모드: 코드 변경 시 자동 리로드 활성화
    # use_reloader=True: Python 파일 변경 감지 및 자동 재시작
    # use_debugger=True: 디버깅 모드 활성화
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True,
        use_reloader=True,
        use_debugger=True
    )


