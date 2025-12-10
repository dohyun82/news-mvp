"""
Purpose: Business logic for log analysis application.

Why: Centralize log analysis and AI-powered CS response generation logic.

How: Integrates Datadog API and OpenAI to analyze logs and generate
CS response suggestions.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from shared.integrations.datadog import query_logs, format_logs_for_analysis
from shared.ai.openai_client import get_summary_from_openai


def query_logs_from_datadog(
    query: str,
    *,
    from_time: Optional[datetime] = None,
    to_time: Optional[datetime] = None,
    limit: int = 100
) -> List[Dict]:
    """Query logs from Datadog.
    
    Args:
        query: Datadog log query string
        from_time: Start time for query
        to_time: End time for query
        limit: Maximum number of logs to return
        
    Returns:
        List of log entries
    """
    return query_logs(query, from_time=from_time, to_time=to_time, limit=limit)


def analyze_logs_with_ai(
    query: str,
    *,
    from_time: Optional[datetime] = None,
    to_time: Optional[datetime] = None,
    limit: int = 100
) -> Dict:
    """Analyze logs using AI and generate CS response suggestions.
    
    Args:
        query: Datadog log query string
        from_time: Start time for query
        to_time: End time for query
        limit: Maximum number of logs to analyze
        
    Returns:
        Dictionary containing:
        - logs: List of log entries
        - summary: AI-generated summary
        - cs_suggestions: CS response suggestions
        - error_patterns: Detected error patterns
    """
    # Datadog에서 로그 조회
    logs = query_logs(query, from_time=from_time, to_time=to_time, limit=limit)
    
    if not logs:
        return {
            "logs": [],
            "summary": "조회된 로그가 없습니다.",
            "cs_suggestions": [],
            "error_patterns": []
        }
    
    # 로그 포맷팅
    formatted_logs = format_logs_for_analysis(logs)
    
    # AI를 사용한 로그 분석
    analysis_prompt = f"""다음은 모바일 식권 애플리케이션의 서버/클라이언트 로그입니다.
이 로그들을 분석하여 다음 정보를 제공해주세요:

1. 주요 에러 및 문제점 요약
2. CS 대응을 위한 제안사항
3. 발견된 에러 패턴

로그:
{formatted_logs[:5000]}  # 최대 5000자로 제한

분석 결과를 한국어로 작성해주세요."""
    
    # OpenAI를 사용한 분석 (요약 함수 재사용)
    analysis_text = get_summary_from_openai("log_analysis", title=analysis_prompt)
    
    # 결과 파싱 (간단한 구조로 반환)
    return {
        "logs": logs,
        "summary": analysis_text,
        "cs_suggestions": _extract_cs_suggestions(analysis_text),
        "error_patterns": _extract_error_patterns(logs)
    }


def _extract_cs_suggestions(analysis_text: str) -> List[str]:
    """Extract CS suggestions from AI analysis text.
    
    Args:
        analysis_text: AI-generated analysis text
        
    Returns:
        List of CS suggestions
    """
    # 간단한 추출 로직 (향후 개선 가능)
    suggestions = []
    lines = analysis_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if line and ('제안' in line or '권장' in line or '대응' in line or '조치' in line):
            # 번호나 불릿 제거
            cleaned = line.lstrip('0123456789.-* ').strip()
            if cleaned:
                suggestions.append(cleaned)
    
    return suggestions[:5]  # 최대 5개


def _extract_error_patterns(logs: List[Dict]) -> List[str]:
    """Extract error patterns from logs.
    
    Args:
        logs: List of log entries
        
    Returns:
        List of error patterns
    """
    patterns = []
    error_keywords = ['error', 'exception', 'failed', 'timeout', '500', '404', '403']
    
    for log in logs[:50]:  # 최대 50개 로그만 분석
        message = log.get("attributes", {}).get("message", log.get("message", "")).lower()
        level = log.get("attributes", {}).get("level", log.get("level", "")).lower()
        
        if level in ['error', 'critical', 'fatal']:
            # 에러 메시지에서 패턴 추출
            for keyword in error_keywords:
                if keyword in message:
                    # 간단한 패턴 추출 (향후 개선 가능)
                    pattern = f"{keyword} 관련 에러 발견"
                    if pattern not in patterns:
                        patterns.append(pattern)
    
    return patterns[:10]  # 최대 10개


__all__ = [
    "query_logs_from_datadog",
    "analyze_logs_with_ai",
]
