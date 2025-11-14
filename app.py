from flask import Flask, jsonify, render_template, request
from modules import crawler, gemini, slack
from modules.store import store
from modules.common import configure_logging, register_http_logging, register_error_handlers

app = Flask(__name__)

# 개발 모드: 템플릿 캐시 비활성화 (코드 변경 즉시 반영)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # 정적 파일 캐시 비활성화

# Common logging / error handling
configure_logging()
register_http_logging(app)
register_error_handlers(app)

@app.route('/api/collect', methods=['POST'])
def collect_news():
    articles = crawler.crawl_naver_news([])
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


