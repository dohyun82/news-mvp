"""
Flask application entry point for vendys-ai-automation-platform.

This module initializes the Flask app and registers Blueprints for different
application modules (news clipping, log analysis, etc.).
"""

from flask import Flask, jsonify, render_template, request, redirect, url_for

# core, shared, apps 모듈 import
from core.common import configure_logging, register_http_logging, register_error_handlers
from apps.news import news_bp

app = Flask(__name__)

# 개발 모드: 템플릿 캐시 비활성화 (코드 변경 즉시 반영)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # 정적 파일 캐시 비활성화

# Common logging / error handling
configure_logging()
register_http_logging(app)
register_error_handlers(app)

# Blueprint 등록
app.register_blueprint(news_bp)

# 하위 호환성: 기존 라우트를 새로운 Blueprint 함수로 위임
# 뉴스 관련 API 라우트 (POST는 리다이렉트 대신 직접 처리)
from apps.news.routes import (
    collect_news_route, summarize_news_route, send_slack_route,
    review_list_route, review_delete_route, review_select_route, review_category_route,
    settings_initial_values_route, settings_save_route, settings_get_route
)

@app.route('/api/collect', methods=['POST'])
def collect_news_legacy():
    """기존 뉴스 수집 API (하위 호환성)."""
    return collect_news_route()

@app.route('/api/summarize', methods=['POST'])
def summarize_news_legacy():
    """기존 뉴스 요약 API (하위 호환성)."""
    return summarize_news_route()

@app.route('/api/send-slack', methods=['POST'])
def send_slack_legacy():
    """기존 슬랙 발송 API (하위 호환성)."""
    return send_slack_route()

@app.route('/api/review/list', methods=['GET'])
def review_list_legacy():
    """기존 뉴스 목록 조회 API (하위 호환성)."""
    return review_list_route()

@app.route('/api/review/delete', methods=['POST'])
def review_delete_legacy():
    """기존 뉴스 삭제 API (하위 호환성)."""
    return review_delete_route()

@app.route('/api/review/select', methods=['POST'])
def review_select_legacy():
    """기존 뉴스 선택/해제 API (하위 호환성)."""
    return review_select_route()

@app.route('/api/review/category', methods=['POST'])
def review_category_legacy():
    """기존 뉴스 카테고리 변경 API (하위 호환성)."""
    return review_category_route()

@app.route('/api/settings/initial-values', methods=['GET'])
def settings_initial_values_legacy():
    """기존 설정 초기값 API (하위 호환성)."""
    return settings_initial_values_route()

@app.route('/api/settings/save', methods=['POST'])
def settings_save_legacy():
    """기존 설정 저장 API (하위 호환성)."""
    return settings_save_route()

@app.route('/api/settings/get', methods=['GET'])
def settings_get_legacy():
    """기존 설정 조회 API (하위 호환성)."""
    return settings_get_route()

# 페이지 라우트 (하위 호환성)
@app.route('/')
def index():
    """메인 대시보드."""
    return render_template('index.html', current_page=None)

@app.route('/review')
def review_page_legacy():
    """기존 뉴스 클리핑 페이지 (하위 호환성)."""
    return redirect(url_for('news.review_page'), code=301)

@app.route('/settings')
def settings_page_legacy():
    """기존 설정 페이지 (하위 호환성)."""
    return redirect(url_for('news.settings_page'), code=301)

if __name__ == '__main__':
    import os

    # 실행 설정은 환경변수로 제어하며 기본값은 안전하게 둔다.
    # 개발 중 디버거/리로더가 필요하면 FLASK_DEBUG=true 로 실행한다.
    # (Werkzeug 디버거를 외부에 노출하면 원격 코드 실행 위험이 있어 기본은 비활성)
    debug_enabled = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(
        host=os.getenv("FLASK_HOST", "127.0.0.1"),
        port=int(os.getenv("FLASK_PORT", "5001")),
        debug=debug_enabled,
        use_reloader=debug_enabled,
        use_debugger=debug_enabled,
    )
