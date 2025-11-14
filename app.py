from flask import Flask, jsonify, render_template, request
from modules import crawler, gemini, slack
from modules.store import store
from modules.common import configure_logging, register_http_logging, register_error_handlers
from modules.config import RealDataConfig

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
}

@app.route('/api/collect', methods=['POST'])
def collect_news():
    # 저장된 사용자 설정 가져오기
    user_keywords = _user_settings["keywords"]
    user_max_articles = _user_settings["max_articles"]
    
    articles = crawler.crawl_naver_news(
        keywords=[],
        user_keywords=user_keywords,
        user_max_articles=user_max_articles
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
    cfg = RealDataConfig()
    return jsonify({
        "keywords": cfg.query_keywords,
        "max_articles": cfg.max_articles,
    })

@app.route('/api/settings/save', methods=['POST'])
def settings_save():
    """사용자 설정을 저장합니다.
    
    요청 본문:
    - keywords: 쉼표로 구분된 키워드 문자열
    - max_articles: 최대 수집 뉴스 개수 (정수)
    """
    try:
        data = request.get_json(silent=True) or {}
        keywords = data.get("keywords")
        max_articles = data.get("max_articles")
        
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
        
        return jsonify({"saved": True})
    except Exception as e:
        import logging
        logging.getLogger("errors").exception("Error in settings_save: %s", e)
        return jsonify({"error": {"type": e.__class__.__name__, "message": str(e)}}), 500

@app.route('/api/settings/get', methods=['GET'])
def settings_get():
    """저장된 사용자 설정을 반환합니다.
    
    저장된 값이 없으면 환경 변수 값을 반환합니다.
    """
    cfg = RealDataConfig()
    keywords = _user_settings["keywords"] if _user_settings["keywords"] is not None else cfg.query_keywords
    max_articles = _user_settings["max_articles"] if _user_settings["max_articles"] is not None else cfg.max_articles
    
    return jsonify({
        "keywords": keywords,
        "max_articles": max_articles,
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


