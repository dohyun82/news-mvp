"""
Purpose: Business logic for log analysis application.

Why: Centralize log analysis and AI-powered CS response generation logic.

How: Integrates Datadog API and OpenAI to analyze logs and generate
CS response suggestions.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from shared.integrations.datadog import query_logs, format_logs_for_analysis
from shared.ai.openai_client import get_summary_from_openai


def _sample_logs_for_analysis(logs: List[Dict], max_samples: int = 30) -> List[Dict]:
    """효율적인 AI 분석을 위해 로그를 샘플링합니다.
    
    전략:
    1. 에러/경고 로그 우선 선택 (중요도 높음)
    2. 시간대별 균등 샘플링 (전체 흐름 파악)
    3. 최대 샘플 수 제한 (성능 최적화)
    
    Args:
        logs: 전체 로그 목록
        max_samples: 최대 샘플 개수 (기본값: 30)
        
    Returns:
        샘플링된 로그 목록
    """
    if not logs:
        return []
    
    if len(logs) <= max_samples:
        return logs
    
    # 1단계: 에러/경고 로그 분리
    error_logs = []
    warning_logs = []
    info_logs = []
    
    for log in logs:
        attributes = log.get("attributes", {})
        level = attributes.get("status", attributes.get("level", "info")).lower()
        
        if level in ["error", "critical", "fatal"]:
            error_logs.append(log)
        elif level in ["warn", "warning"]:
            warning_logs.append(log)
        else:
            info_logs.append(log)
    
    # 2단계: 샘플링 전략 (에러 로그 우선 집중)
    sampled = []
    
    # 에러 로그는 최대 40% 할당 (중요도 높음, 더 집중)
    error_quota = int(max_samples * 0.4)
    if error_logs:
        # 에러 로그가 많으면 시간순으로 균등 샘플링
        if len(error_logs) > error_quota:
            step = len(error_logs) / error_quota
            sampled.extend([error_logs[int(i * step)] for i in range(error_quota)])
        else:
            sampled.extend(error_logs)
    
    # 경고 로그는 최대 30% 할당
    warning_quota = int(max_samples * 0.3)
    if warning_logs and len(sampled) < max_samples:
        remaining_quota = min(warning_quota, max_samples - len(sampled))
        if len(warning_logs) > remaining_quota:
            step = len(warning_logs) / remaining_quota
            sampled.extend([warning_logs[int(i * step)] for i in range(remaining_quota)])
        else:
            sampled.extend(warning_logs[:remaining_quota])
    
    # 정보 로그는 나머지 할당 (시간순 균등 샘플링)
    remaining_quota = max_samples - len(sampled)
    if info_logs and remaining_quota > 0:
        if len(info_logs) > remaining_quota:
            step = len(info_logs) / remaining_quota
            sampled.extend([info_logs[int(i * step)] for i in range(remaining_quota)])
        else:
            sampled.extend(info_logs[:remaining_quota])
    
    # 시간순 정렬 (원본 순서 유지)
    return sampled[:max_samples]


def build_datadog_query(
    *,
    user_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    service: Optional[str] = None,
    app_installation: Optional[str] = None,
    additional_query: Optional[str] = None
) -> str:
    """Build Datadog query string from filter parameters.
    
    필터 파라미터를 Datadog 쿼리 문자열로 변환합니다.
    사용자 ID와 고객사 ID는 Datadog의 attributes 필드로 저장되어 있다고 가정합니다.
    
    Args:
        user_id: 사용자 ID 필터 (ua-user-id 필드)
        customer_id: 고객사 ID 필터 (ua-com-id 필드)
        service: 서비스 필터 (service 필드, 쉼표로 구분된 여러 서비스 지원)
        app_installation: 앱 설치 ID 필터 (app-installation 필드)
        additional_query: 추가 쿼리 텍스트 (기존 텍스트 쿼리 방식)
        
    Returns:
        Datadog 쿼리 문자열
        
    Example:
        >>> query = build_datadog_query(user_id="12345", service="payment-service")
        >>> # Returns: "service:payment-service @ua-user-id:12345"
    """
    query_parts = []
    
    # 서비스 필터 추가 (우선순위가 높으므로 먼저 추가)
    if service:
        service = service.strip()
        # 쉼표로 구분된 여러 서비스 지원
        if ',' in service:
            # 여러 서비스는 OR 조건으로 처리: service:(payment-service OR websocket-service)
            services = [s.strip() for s in service.split(',') if s.strip()]
            if services:
                service_query = " OR ".join(services)
                query_parts.append(f"service:({service_query})")
        else:
            query_parts.append(f"service:{service}")
    
    # 사용자 ID 필터 추가
    if user_id:
        query_parts.append(f"@ua-user-id:{user_id}")
    
    # 고객사 ID 필터 추가
    if customer_id:
        query_parts.append(f"@ua-com-id:{customer_id}")
    
    # 앱 설치 ID 필터 추가
    if app_installation:
        query_parts.append(f"@app-installation:{app_installation}")
    
    # 추가 쿼리 텍스트가 있으면 추가
    if additional_query:
        query_parts.append(additional_query.strip())
    
    # 쿼리 파트를 공백으로 연결
    query = " ".join(query_parts)
    
    # 기본 서비스 필터가 없으면 추가 (sikdae-android와 sikdae-ios 로그만 조회)
    if not query or "service:" not in query.lower():
        # 기본값: sikdae-android 또는 sikdae-ios
        default_service = "service:(sikdae-android OR sikdae-ios)"
        if query:
            query = f"{default_service} {query}"
        else:
            query = default_service
    
    return query


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
    limit: int = 200,
    user_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    service: Optional[str] = None,
    app_installation: Optional[str] = None,
    cs_content: Optional[str] = None
) -> Dict:
    """Analyze logs using AI and generate structured CS response suggestions.
    
    CS 담당자가 고객 CS 대응 시 사용할 수 있도록 로그를 분석하고
    구조화된 결과를 제공합니다.
    
    Args:
        query: Datadog log query string (또는 빈 문자열인 경우 필터로 쿼리 생성)
        from_time: Start time for query
        to_time: End time for query
        limit: Maximum number of logs to analyze
        user_id: 사용자 ID (쿼리 생성 시 사용)
        customer_id: 고객사 ID (쿼리 생성 시 사용)
        service: 서비스 이름 (쿼리 생성 시 사용, 쉼표로 구분된 여러 서비스 지원)
        app_installation: 앱 설치 ID (쿼리 생성 시 사용)
        cs_content: 고객 CS 내용 (선택사항, AI 분석 시 함께 고려)
        
    Returns:
        Dictionary containing:
        - logs: List of log entries
        - problem_summary: 문제점 요약
        - root_cause: 원인 추적 분석
        - user_behavior: 사용자 행동 분석
        - cs_suggestions: CS 대응 제안 (리스트)
        - error_patterns: 발견된 에러 패턴 (리스트)
    """
    # 쿼리가 비어있고 필터 파라미터가 있으면 쿼리 생성
    if not query.strip() and (user_id or customer_id or service or app_installation):
        query = build_datadog_query(
            user_id=user_id,
            customer_id=customer_id,
            service=service,
            app_installation=app_installation
        )
    
    # Datadog에서 로그 조회
    logs = query_logs(query, from_time=from_time, to_time=to_time, limit=limit)
    
    if not logs:
        return {
            "logs": [],
            "problem_summary": "조회된 로그가 없습니다.",
            "root_cause": "",
            "user_behavior": "",
            "cs_suggestions": [],
            "error_patterns": []
        }
    
    # 1단계: 로컬 전처리 - 에러/경고 로그만 추출 (핵심만 분석)
    # 하지만 그룹화를 위해 모든 로그를 고려하되, 에러/경고는 별도로 플래그 처리
    
    # 2단계: 로그 패턴 그룹화 (개선된 로직)
    # 최대 500개의 로그를 가져왔다고 가정하고 패턴 분석 수행
    grouped_patterns = _group_logs_by_pattern(logs)
    total_patterns = len(grouped_patterns)
    
    # AI 프롬프트 생성을 위한 요약문 작성
    pattern_summary, patterns_included = _format_patterns_for_ai(grouped_patterns)
    
    # 로그 샘플 (최대 10개, 원본 확인용)
    sample_logs_text = format_logs_for_analysis(logs[:10])
    
    # 텍스트 길이 제한
    if len(pattern_summary) > 15000:
        pattern_summary = pattern_summary[:15000] + "...(truncated)"
    
    # CS 내용 간소화 (500자로 제한)
    cs_context = ""
    if cs_content:
        cs_content_short = cs_content[:500]
        if len(cs_content) > 500:
            cs_content_short += "..."
        cs_context = f"\n\n고객 문의: {cs_content_short}"
    
    # 최소한의 프롬프트 생성 (핵심만)
    analysis_prompt = f"""로그 분석 요청입니다.{cs_context}

분석 대상 로그 요약 (총 {len(logs)}건 분석됨):

{pattern_summary}

참고용 최신 원본 로그 (10건):
{sample_logs_text}

다음 형식으로 분석해주세요:

## 문제점 요약
(발생 빈도가 높거나 심각한 에러 패턴 위주로 요약)

## 원인 추적
(타임라인 기반으로 어떤 패턴이 문제를 유발했는지 추론)

## 사용자 행동 분석
(로그 패턴을 통해 사용자가 어떤 행동을 하다가 문제가 발생했는지 분석)

## CS 대응 제안
(구체적 대응 방안 번호로 나열)

한국어로 간결하게 작성해주세요."""
    
    # OpenAI를 사용한 분석 (타임아웃 90초, 기존 모델 유지)
    analysis_text = get_summary_from_openai(
        "log_analysis", 
        title=analysis_prompt, 
        timeout_seconds=90
    )
    
    # 구조화된 결과 파싱
    parsed_result = _parse_structured_analysis(analysis_text)
    
    return {
        "logs": logs,
        "problem_summary": parsed_result.get("problem_summary", ""),
        "root_cause": parsed_result.get("root_cause", ""),
        "user_behavior": parsed_result.get("user_behavior", ""),
        "cs_suggestions": parsed_result.get("cs_suggestions", []),
        "error_patterns": _extract_error_patterns(logs),
        # 패턴 그룹화 통계 정보 추가
        "pattern_stats": {
            "total_logs": len(logs),
            "total_patterns": total_patterns,
            "patterns_included_in_ai": patterns_included,
            "original_logs_sent": min(10, len(logs))
        }
    }


def _parse_structured_analysis(analysis_text: str) -> Dict[str, str | List[str]]:
    """Parse structured analysis text from OpenAI into sections.
    
    OpenAI 응답을 파싱하여 문제점 요약, 원인 추적, 사용자 행동 분석,
    CS 대응 제안을 추출합니다.
    
    Args:
        analysis_text: AI-generated structured analysis text
        
    Returns:
        Dictionary containing:
        - problem_summary: 문제점 요약 텍스트
        - root_cause: 원인 추적 텍스트
        - user_behavior: 사용자 행동 분석 텍스트
        - cs_suggestions: CS 대응 제안 리스트
    """
    result = {
        "problem_summary": "",
        "root_cause": "",
        "user_behavior": "",
        "cs_suggestions": []
    }
    
    if not analysis_text:
        return result
    
    # 섹션별로 분리 (마크다운 헤더 또는 텍스트 패턴 사용)
    sections = {
        "problem_summary": [
            r"##\s*문제점\s*요약",
            r"##\s*주요\s*에러",
            r"##\s*문제점",
            r"문제점\s*요약",
            r"주요\s*에러"
        ],
        "root_cause": [
            r"##\s*원인\s*추적",
            r"##\s*원인",
            r"원인\s*추적",
            r"원인\s*분석"
        ],
        "user_behavior": [
            r"##\s*사용자\s*행동\s*분석",
            r"##\s*사용자\s*행동",
            r"사용자\s*행동\s*분석",
            r"사용자\s*행동"
        ],
        "cs_suggestions": [
            r"##\s*CS\s*대응\s*제안",
            r"##\s*대응\s*제안",
            r"CS\s*대응\s*제안",
            r"대응\s*제안",
            r"제안사항"
        ]
    }
    
    lines = analysis_text.split('\n')
    current_section = None
    current_content = []
    
    for line in lines:
        line_stripped = line.strip()
        
        # 섹션 헤더 확인
        section_found = False
        for section_name, patterns in sections.items():
            for pattern in patterns:
                if re.search(pattern, line_stripped, re.IGNORECASE):
                    # 이전 섹션 저장
                    if current_section and current_content:
                        content = '\n'.join(current_content).strip()
                        if current_section == "cs_suggestions":
                            result[current_section] = _extract_cs_suggestions(content)
                        else:
                            result[current_section] = content
                    
                    # 새 섹션 시작
                    current_section = section_name
                    current_content = []
                    section_found = True
                    break
            
            if section_found:
                break
        
        # 섹션 헤더가 아니면 내용 추가
        if not section_found and current_section:
            # 헤더 라인은 제외
            if not line_stripped.startswith('#'):
                current_content.append(line)
    
    # 마지막 섹션 저장
    if current_section and current_content:
        content = '\n'.join(current_content).strip()
        if current_section == "cs_suggestions":
            result[current_section] = _extract_cs_suggestions(content)
        else:
            result[current_section] = content
    
    # 파싱이 실패한 경우 전체 텍스트를 요약으로 사용
    if not result["problem_summary"] and not result["root_cause"]:
        # 간단한 파싱 시도: 첫 500자를 요약으로
        result["problem_summary"] = analysis_text[:500].strip()
    
    return result


def _extract_cs_suggestions(analysis_text: str) -> List[str]:
    """Extract CS suggestions from AI analysis text.
    
    Args:
        analysis_text: AI-generated analysis text (CS 대응 제안 섹션)
        
    Returns:
        List of CS suggestions
    """
    suggestions = []
    lines = analysis_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 번호가 있는 항목 추출 (1., 2., - 등)
        # 또는 "제안", "권장", "대응", "조치" 키워드가 있는 라인
        if (
            re.match(r'^\d+[\.\)]\s+', line) or
            re.match(r'^[-*]\s+', line) or
            any(keyword in line for keyword in ['제안', '권장', '대응', '조치', '방안', '안내'])
        ):
            # 번호나 불릿 제거
            cleaned = re.sub(r'^\d+[\.\)]\s+', '', line)
            cleaned = re.sub(r'^[-*]\s+', '', cleaned)
            cleaned = cleaned.strip()
            
            if cleaned and len(cleaned) > 10:  # 최소 길이 체크
                suggestions.append(cleaned)
    
    # 최대 10개로 제한
    return suggestions[:10]


def _extract_error_summary_locally(logs: List[Dict]) -> str:
    """로컬에서 에러 요약을 추출하여 AI 프롬프트 크기를 줄입니다.
    
    AI에 전송하기 전에 로컬에서 먼저 에러 패턴을 요약하여
    프롬프트 크기를 대폭 줄이고 처리 시간을 단축합니다.
    
    Args:
        logs: 에러/경고 로그 목록 (최대 50개 권장)
        
    Returns:
        에러 요약 텍스트 (최대 500자)
    """
    if not logs:
        return "에러 로그 없음"
    
    error_types = {}
    error_messages = []
    warning_count = 0
    
    for log in logs[:50]:  # 최대 50개만 분석
        attributes = log.get("attributes", {})
        nested_attrs = attributes.get("attributes", {})
        level = attributes.get("status") or nested_attrs.get("status") or attributes.get("level") or "info"
        level = level.lower()
        
        message = nested_attrs.get("message") or attributes.get("message") or log.get("message", "")
        
        if level in ["error", "critical", "fatal"]:
            # 에러 타입 분류
            error_key = "unknown"
            if "timeout" in message.lower():
                error_key = "timeout"
            elif "404" in message or "not found" in message.lower():
                error_key = "404_not_found"
            elif "500" in message or "internal" in message.lower():
                error_key = "500_internal_error"
            elif "403" in message or "forbidden" in message.lower():
                error_key = "403_forbidden"
            elif "network" in message.lower() or "connection" in message.lower():
                error_key = "network_error"
            elif "payment" in message.lower() or "결제" in message:
                error_key = "payment_error"
            
            error_types[error_key] = error_types.get(error_key, 0) + 1
            
            # 에러 메시지 샘플 (최대 3개)
            if len(error_messages) < 3 and message:
                msg_short = message[:100]
                error_messages.append(msg_short)
        elif level in ["warn", "warning"]:
            warning_count += 1
    
    # 요약 생성
    summary_parts = []
    
    if error_types:
        summary_parts.append(f"에러 유형: {', '.join([f'{k}({v}회)' for k, v in error_types.items()])}")
    
    if warning_count > 0:
        summary_parts.append(f"경고: {warning_count}개")
    
    if error_messages:
        summary_parts.append(f"주요 에러: {' | '.join(error_messages)}")
    
    summary = " | ".join(summary_parts)
    
    # 최대 500자로 제한
    return summary[:500] if len(summary) > 500 else summary


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


def _normalize_log_message(message: str) -> str:
    """Normalize log message to create a pattern signature.
    
    Removes variable parts like IDs, timestamps, IP addresses, etc.
    
    Args:
        message: Raw log message
        
    Returns:
        Normalized message signature
    """
    if not message:
        return ""
        
    # 1. UUID/GUID (e.g., 123e4567-e89b-12d3-a456-426614174000)
    message = re.sub(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', '<UUID>', message)
    
    # 2. IP Address (IPv4)
    message = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', '<IP>', message)
    
    # 3. Date/Time (ISO-like patterns)
    message = re.sub(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?', '<DATE>', message)
    
    # 4. Sequences of numbers (IDs, excessive digits) - 3자리 이상
    message = re.sub(r'\b\d{3,}\b', '<NUM>', message)
    
    # 5. Hex strings (memory addresses, hashes) - e.g. 0x123abc
    message = re.sub(r'0x[0-9a-fA-F]+', '<HEX>', message)
    
    # 6. User IDs inside brackets or similar (specific to app logs)
    # e.g., [u:12345] -> [u:<NUM>]
    
    return message.strip()


def _group_logs_by_pattern(logs: List[Dict]) -> List[Dict]:
    """Group logs by their normalized pattern.
    
    Args:
        logs: List of log entries
        
    Returns:
        List of pattern groups, sorted by count (descending) and importance (errors first)
    """
    groups = {}
    
    for log in logs:
        attributes = log.get("attributes", {})
        nested_attrs = attributes.get("attributes", {})
        
        # 기본 속성 추출
        service = attributes.get("service", log.get("service", "unknown"))
        status = attributes.get("status") or nested_attrs.get("status") or attributes.get("level") or "info"
        status = status.upper()
        
        # 메시지 추출
        original_message = nested_attrs.get("message") or attributes.get("message") or log.get("message", "")
        if len(original_message) > 500:
            original_message = original_message[:500] + "..."
            
        # 정규화
        normalized_msg = _normalize_log_message(original_message)
        
        # 시그니처 키 생성 (Service + Status + Normalized Message)
        signature = f"{service}|{status}|{normalized_msg}"
        
        if signature not in groups:
            groups[signature] = {
                "signature": signature,
                "service": service,
                "status": status,
                "pattern_message": normalized_msg,
                "count": 0,
                "first_seen": None,
                "last_seen": None,
                "sample_messages": [],
                "user_ids": set(),
            }
            
        group = groups[signature]
        group["count"] += 1
        
        # 타임스탬프 처리
        timestamp = (
            nested_attrs.get("app-timestamp") or 
            attributes.get("app-timestamp") or 
            attributes.get("timestamp") or 
            log.get("timestamp")
        )
        # 타임스탬프 파싱 (문자열인 경우만)
        if isinstance(timestamp, str):
            try:
                ts_val = timestamp.replace('Z', '+00:00')[:19] # 초 단위까지만
            except:
                ts_val = str(timestamp)
        else:
            ts_val = str(timestamp)
            
        if group["first_seen"] is None or ts_val < group["first_seen"]:
            group["first_seen"] = ts_val
        if group["last_seen"] is None or ts_val > group["last_seen"]:
            group["last_seen"] = ts_val
            
        # 샘플 메시지 저장 (최대 3개, 서로 다른 내용만)
        if len(group["sample_messages"]) < 3:
            if original_message not in group["sample_messages"]:
                group["sample_messages"].append(original_message)
                
        # 사용자 ID 수집 (영향받은 사용자 수 파악용, 최대 5개)
        user_id = nested_attrs.get("ua-user-id") or attributes.get("ua-user-id")
        if user_id and len(group["user_ids"]) < 5:
            group["user_ids"].add(str(user_id))
            
    # 리스트로 변환 및 정렬
    # 정렬 우선순위: 1. 에러/경고 여부, 2. 발생 횟수
    pattern_list = list(groups.values())
    
    def sort_key(item):
        is_error = 1 if item["status"] in ["ERROR", "CRITICAL", "FATAL", "WARN", "WARNING"] else 0
        return (is_error, item["count"])
        
    pattern_list.sort(key=sort_key, reverse=True)
    
    return pattern_list


def _format_patterns_for_ai(patterns: List[Dict]) -> Tuple[str, int]:
    """Format log patterns for AI prompt.
    
    패턴 개수를 동적으로 조정합니다:
    - 패턴이 20개 이하: 모두 포함
    - 패턴이 21-50개: 상위 30개 포함
    - 패턴이 51개 이상: 상위 40개 포함
    
    Args:
        patterns: List of log pattern groups
        
    Returns:
        Tuple of (formatted string description of patterns, number of patterns included)
    """
    lines = []
    
    # 동적 패턴 개수 조정
    if len(patterns) <= 20:
        max_patterns = len(patterns)
    elif len(patterns) <= 50:
        max_patterns = 30
    else:
        max_patterns = 40
    
    included_patterns = patterns[:max_patterns]
    
    for i, p in enumerate(included_patterns, 1):
        users_affected = f", Affected Users: {len(p['user_ids'])}+" if p['user_ids'] else ""
        lines.append(f"{i}. [{p['status']}] {p['service']} (Count: {p['count']}{users_affected})")
        lines.append(f"   Time: {p['first_seen']} ~ {p['last_seen']}")
        lines.append(f"   Pattern: {p['pattern_message']}")
        
        # 샘플 하나만 표시
        if p['sample_messages']:
             lines.append(f"   Sample: {p['sample_messages'][0]}")
        lines.append("")
        
    if len(patterns) > max_patterns:
        lines.append(f"... and {len(patterns) - max_patterns} more patterns.")
        
    return "\n".join(lines), max_patterns


__all__ = [
    "build_datadog_query",
    "query_logs_from_datadog",
    "analyze_logs_with_ai",
    "_sample_logs_for_analysis",  # 내부 함수지만 테스트용으로 export
]
