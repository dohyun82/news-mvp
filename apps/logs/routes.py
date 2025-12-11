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
from .services import build_datadog_query, query_logs_from_datadog, analyze_logs_with_ai
from shared.integrations.datadog import query_logs, format_logs_for_analysis
from shared.ai.openai_client import get_summary_from_openai


@logs_bp.route('')
def index():
    """로그 분석 대시보드 페이지."""
    return render_template('logs.html', current_page='logs')


@logs_bp.route('/api/query', methods=['POST', 'OPTIONS'])
def query_logs_route():
    """Datadog 로그 쿼리 API.
    
    필터 기반 쿼리 또는 텍스트 쿼리를 지원합니다.
    
    요청 본문:
    - query: Datadog 쿼리 문자열 (선택사항, 필터와 함께 사용 가능)
    - user_id: 사용자 ID 필터 (ua-user-id)
    - customer_id: 고객사 ID 필터 (ua-com-id)
    - service: 서비스 필터 (service)
    - app_installation: 앱 설치 ID 필터 (app-installation)
    - from_time: 시작 시간 (ISO 8601 형식, 선택사항)
    - to_time: 종료 시간 (ISO 8601 형식, 선택사항)
    - limit: 최대 로그 개수 (기본값: 100)
    
    Note: query가 없고 필터도 없으면 에러 반환
    """
    # CORS preflight 요청 처리
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response
    
    try:
        data = request.get_json(silent=True) or {}
        query = data.get("query", "").strip()
        user_id = data.get("user_id", "").strip() or None
        customer_id = data.get("customer_id", "").strip() or None
        service = data.get("service", "").strip() or None
        app_installation = data.get("app_installation", "").strip() or None
        
        # 쿼리 또는 필터가 있어야 함
        if not query and not user_id and not customer_id and not service and not app_installation:
            return jsonify({"error": "query or filter (user_id/customer_id/service/app_installation) is required"}), 400
        
        # 필터가 있으면 쿼리 생성
        if user_id or customer_id or service or app_installation:
            query = build_datadog_query(
                user_id=user_id,
                customer_id=customer_id,
                service=service,
                app_installation=app_installation,
                additional_query=query if query else None
            )
        
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
        
        # Datadog 요청 파라미터 로깅
        logger = logging.getLogger("logs")
        logger.info(
            "Datadog 로그 조회 요청 - query: %s, from_time: %s, to_time: %s, limit: %d",
            query,
            from_time.isoformat() if from_time else None,
            to_time.isoformat() if to_time else None,
            limit
        )
        
        # Datadog에서 로그 조회
        logs = query_logs(query, from_time=from_time, to_time=to_time, limit=limit)
        
        # 조회 결과 로깅
        logger.info("Datadog 로그 조회 완료 - 조회된 로그 개수: %d", len(logs))
        
        return jsonify({
            "logs": logs,
            "count": len(logs),
            "query": query
        })
    except Exception as e:
        logging.getLogger("errors").exception("Error in query_logs_route: %s", e)
        return jsonify({"error": {"type": e.__class__.__name__, "message": str(e)}}), 500


@logs_bp.route('/api/analyze', methods=['POST', 'OPTIONS'])
def analyze_logs_route():
    """AI 기반 로그 분석 API.
    
    필터 기반 쿼리 또는 텍스트 쿼리를 지원하며, 구조화된 분석 결과를 반환합니다.
    
    요청 본문:
    - query: Datadog 쿼리 문자열 (선택사항, 필터와 함께 사용 가능)
    - user_id: 사용자 ID 필터 (ua-user-id)
    - customer_id: 고객사 ID 필터 (ua-com-id)
    - service: 서비스 필터 (service)
    - app_installation: 앱 설치 ID 필터 (app-installation)
    - cs_content: 고객 CS 내용 (선택사항, AI 분석 시 함께 고려)
    - from_time: 시작 시간 (ISO 8601 형식, 선택사항)
    - to_time: 종료 시간 (ISO 8601 형식, 선택사항)
    - limit: 최대 로그 개수 (기본값: 100)
    
    Returns:
        구조화된 AI 분석 결과:
        - logs: 로그 목록
        - problem_summary: 문제점 요약
        - root_cause: 원인 추적
        - user_behavior: 사용자 행동 분석
        - cs_suggestions: CS 대응 제안 리스트
        - error_patterns: 에러 패턴 리스트
    
    Note: query가 없고 필터도 없으면 에러 반환
    """
    # CORS preflight 요청 처리
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response
    
    try:
        data = request.get_json(silent=True) or {}
        query = data.get("query", "").strip()
        user_id = data.get("user_id", "").strip() or None
        customer_id = data.get("customer_id", "").strip() or None
        service = data.get("service", "").strip() or None
        app_installation = data.get("app_installation", "").strip() or None
        cs_content = data.get("cs_content", "").strip() or None
        
        # 쿼리 또는 필터가 있어야 함
        if not query and not user_id and not customer_id and not service and not app_installation:
            return jsonify({"error": "query or filter (user_id/customer_id/service/app_installation) is required"}), 400
        
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
        
        # 로그 분석 수행 (필터 파라미터 및 CS 내용 전달)
        analysis_result = analyze_logs_with_ai(
            query=query,
            from_time=from_time,
            to_time=to_time,
            limit=limit,
            user_id=user_id,
            customer_id=customer_id,
            service=service,
            app_installation=app_installation,
            cs_content=cs_content
        )
        
        return jsonify(analysis_result)
    except Exception as e:
        logging.getLogger("errors").exception("Error in analyze_logs_route: %s", e)
        return jsonify({"error": {"type": e.__class__.__name__, "message": str(e)}}), 500
