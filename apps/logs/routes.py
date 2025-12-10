"""
Purpose: Routes for log analysis application.

Why: Centralize all log analysis-related routes in the logs Blueprint.

How: Define routes with /logs prefix for Datadog log query and AI analysis.
"""

from __future__ import annotations

import logging
from flask import jsonify, render_template, request
from datetime import datetime, timedelta

from . import logs_bp
from .services import query_logs_from_datadog, analyze_logs_with_ai
from shared.integrations.datadog import query_logs, format_logs_for_analysis
from shared.ai.openai_client import get_summary_from_openai


@logs_bp.route('')
def index():
    """로그 분석 대시보드 페이지."""
    return render_template('index.html', current_page='logs')


@logs_bp.route('/api/query', methods=['POST'])
def query_logs_route():
    """Datadog 로그 쿼리 API.
    
    요청 본문:
    - query: Datadog 쿼리 문자열 (예: "service:mobile-app status:error")
    - from_time: 시작 시간 (ISO 8601 형식, 선택사항)
    - to_time: 종료 시간 (ISO 8601 형식, 선택사항)
    - limit: 최대 로그 개수 (기본값: 100)
    """
    try:
        data = request.get_json(silent=True) or {}
        query = data.get("query", "")
        
        if not query:
            return jsonify({"error": "query is required"}), 400
        
        # 시간 파라미터 파싱
        from_time = None
        to_time = None
        if data.get("from_time"):
            try:
                from_time = datetime.fromisoformat(data["from_time"].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({"error": "invalid from_time format. Use ISO 8601 format"}), 400
        
        if data.get("to_time"):
            try:
                to_time = datetime.fromisoformat(data["to_time"].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({"error": "invalid to_time format. Use ISO 8601 format"}), 400
        
        limit = data.get("limit", 100)
        if not isinstance(limit, int) or limit <= 0:
            return jsonify({"error": "limit must be a positive integer"}), 400
        
        # Datadog에서 로그 조회
        logs = query_logs(query, from_time=from_time, to_time=to_time, limit=limit)
        
        return jsonify({
            "logs": logs,
            "count": len(logs),
            "query": query
        })
    except Exception as e:
        logging.getLogger("errors").exception("Error in query_logs_route: %s", e)
        return jsonify({"error": {"type": e.__class__.__name__, "message": str(e)}}), 500


@logs_bp.route('/api/analyze', methods=['POST'])
def analyze_logs_route():
    """AI 기반 로그 분석 API.
    
    요청 본문:
    - query: Datadog 쿼리 문자열
    - from_time: 시작 시간 (ISO 8601 형식, 선택사항)
    - to_time: 종료 시간 (ISO 8601 형식, 선택사항)
    - limit: 최대 로그 개수 (기본값: 100)
    
    Returns:
        AI 분석 결과 및 CS 대응 제안
    """
    try:
        data = request.get_json(silent=True) or {}
        query = data.get("query", "")
        
        if not query:
            return jsonify({"error": "query is required"}), 400
        
        # 시간 파라미터 파싱
        from_time = None
        to_time = None
        if data.get("from_time"):
            try:
                from_time = datetime.fromisoformat(data["from_time"].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({"error": "invalid from_time format. Use ISO 8601 format"}), 400
        
        if data.get("to_time"):
            try:
                to_time = datetime.fromisoformat(data["to_time"].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({"error": "invalid to_time format. Use ISO 8601 format"}), 400
        
        limit = data.get("limit", 100)
        if not isinstance(limit, int) or limit <= 0:
            return jsonify({"error": "limit must be a positive integer"}), 400
        
        # 로그 분석 수행
        analysis_result = analyze_logs_with_ai(query, from_time=from_time, to_time=to_time, limit=limit)
        
        return jsonify(analysis_result)
    except Exception as e:
        logging.getLogger("errors").exception("Error in analyze_logs_route: %s", e)
        return jsonify({"error": {"type": e.__class__.__name__, "message": str(e)}}), 500
