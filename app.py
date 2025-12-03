from flask import Flask, jsonify, render_template, request
from modules import crawler, openai, slack
from modules.store import store
from modules.common import configure_logging, register_http_logging, register_error_handlers
from modules.config import RealDataConfig
from modules import keyword_store

app = Flask(__name__)

# 개발 모드: 템플릿 캐시 비활성화 (코드 변경 즉시 반영)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # 정적 파일 캐시 비활성화

# Common logging / error handling
configure_logging()
register_http_logging(app)
register_error_handlers(app)

# 키워드 설정은 keyword_store 모듈(JSON 파일 기반)을 통해 관리됩니다.
# 서버 재시작 시에도 설정이 유지됩니다.

@app.route('/api/collect', methods=['POST'])
def collect_news():
    """뉴스 수집 API.
    
    keyword_store에서 키워드 설정을 읽어와 뉴스를 수집합니다.
    """
    # keyword_store에서 설정 가져오기 (None 전달하여 keyword_store의 기본값 사용)
    articles = crawler.crawl_naver_news(
        keywords=[],
        user_keywords=None,  # None이면 keyword_store에서 읽어옴
        user_max_articles=None,  # None이면 keyword_store에서 읽어옴
        user_category_keywords=None,  # None이면 keyword_store에서 읽어옴
        user_max_age_hours=None  # None이면 keyword_store에서 읽어옴
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
    
    # OpenAI API 호출 (제목이 있으면 함께 전달)
    summary = openai.get_summary_from_openai(url, title=title)
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
    """keyword_store에서 초기값을 읽어서 반환합니다.
    
    로컬 스토리지에 값이 없을 때만 사용됩니다.
    """
    return jsonify({
        "keywords": keyword_store.get_query_keywords(),
        "max_articles": keyword_store.get_max_articles(),
        "category_keywords": keyword_store.get_category_keywords(),
        "max_age_hours": keyword_store.get_max_age_hours(),
    })

@app.route('/api/settings/save', methods=['POST'])
def settings_save():
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
        
        # 검증 및 저장
        if keywords is not None:
            if not isinstance(keywords, str):
                return jsonify({"error": "keywords must be a string"}), 400
            if not keyword_store.update_query_keywords(keywords):
                return jsonify({"error": "failed to save keywords"}), 500
        
        if max_articles is not None:
            try:
                max_articles = int(max_articles)
                if max_articles <= 0:
                    return jsonify({"error": "max_articles must be a positive integer"}), 400
            except (ValueError, TypeError):
                return jsonify({"error": "max_articles must be an integer"}), 400
            if not keyword_store.update_max_articles(max_articles):
                return jsonify({"error": "failed to save max_articles"}), 500
        
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
            if not keyword_store.update_category_keywords(category_keywords):
                return jsonify({"error": "failed to save category_keywords"}), 500
        
        if max_age_hours is not None:
            try:
                max_age_hours = int(max_age_hours)
                if max_age_hours < 0:
                    return jsonify({"error": "max_age_hours must be 0 or greater"}), 400
            except (ValueError, TypeError):
                return jsonify({"error": "max_age_hours must be an integer"}), 400
            if not keyword_store.update_max_age_hours(max_age_hours):
                return jsonify({"error": "failed to save max_age_hours"}), 500
        
        return jsonify({"saved": True})
    except Exception as e:
        import logging
        logging.getLogger("errors").exception("Error in settings_save: %s", e)
        return jsonify({"error": {"type": e.__class__.__name__, "message": str(e)}}), 500

@app.route('/api/settings/get', methods=['GET'])
def settings_get():
    """keyword_store에서 저장된 설정을 반환합니다.
    
    모든 설정은 keyword_store(JSON 파일)에서 읽어옵니다.
    """
    return jsonify({
        "keywords": keyword_store.get_query_keywords(),
        "max_articles": keyword_store.get_max_articles(),
        "category_keywords": keyword_store.get_category_keywords(),
        "max_age_hours": keyword_store.get_max_age_hours(),
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


