"""
Flask application entry point for vendys-ai-automation-platform.

This module initializes the Flask app and registers Blueprints for different
application modules (news clipping, log analysis, etc.).
"""

from flask import Flask, jsonify, render_template, request, redirect, url_for

# 점진적 마이그레이션: 기존 modules를 import하여 하위 호환성 유지
from modules import crawler, openai, slack
from modules.store import store
from modules.common import configure_logging, register_http_logging, register_error_handlers
from modules.config import RealDataConfig
from modules import keyword_store

# 새로운 구조: core, shared, apps 모듈 import
from core.common import configure_logging as configure_logging_new, register_http_logging as register_http_logging_new, register_error_handlers as register_error_handlers_new
from apps.news import news_bp
from apps.logs import logs_bp

app = Flask(__name__)

# 개발 모드: 템플릿 캐시 비활성화 (코드 변경 즉시 반영)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # 정적 파일 캐시 비활성화

# Common logging / error handling (새로운 구조 사용)
configure_logging_new()
register_http_logging_new(app)
register_error_handlers_new(app)

# Blueprint 등록
app.register_blueprint(news_bp)
app.register_blueprint(logs_bp)

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

@app.route('/logs')
def logs_page_legacy():
    """기존 로그 분석 페이지 (하위 호환성)."""
    return redirect(url_for('logs.index'), code=301)

@app.route('/settings')
def settings_page_legacy():
    """기존 설정 페이지 (하위 호환성)."""
    return redirect(url_for('news.settings_page'), code=301)

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
