"""
Purpose: Datadog API integration for log analysis.

Why: Provide a unified interface to query Datadog logs for mobile app
server/client logs to support CS response automation.

How: Use Datadog API to query logs and retrieve relevant log entries
for analysis.
"""

from __future__ import annotations

import base64
import gzip
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from core.config import DatadogConfig


def _try_decode_gzip_body(log: Dict) -> None:
    """Try to decode gzip compressed http-response-body in log attributes."""
    try:
        attributes = log.get("attributes", {})
        # Check standard location and nested location
        body = attributes.get("http-response-body")
        
        # If not found in top level, check nested attributes
        if not body:
            nested_attrs = attributes.get("attributes", {})
            body = nested_attrs.get("http-response-body")
            
        if body and isinstance(body, str):
            # Try to decode base64 and decompress gzip
            try:
                compressed_data = base64.b64decode(body)
                decompressed_data = gzip.decompress(compressed_data)
                decoded_text = decompressed_data.decode('utf-8')
                
                # Check if it's JSON
                try:
                    json_data = json.loads(decoded_text)
                    # Store decoded data in a new field
                    log["decoded_response_body"] = json_data
                except json.JSONDecodeError:
                    # If not JSON, store as text
                    log["decoded_response_body"] = decoded_text
            except (base64.binascii.Error, gzip.BadGzipFile, UnicodeDecodeError):
                # Valid string but not gzip/base64, ignore
                pass
    except Exception:
        # Fail silently for any other errors to not disrupt log flow
        pass


def query_logs(
    query: str,
    *,
    from_time: Optional[datetime] = None,
    to_time: Optional[datetime] = None,
    limit: int = 100,
    timeout_seconds: int = 30
) -> List[Dict]:
    """Query logs from Datadog.
    
    Args:
        query: Datadog log query string (e.g., "service:sikdae-android status:error")
        from_time: Start time for query (default: 1 hour ago)
        to_time: End time for query (default: now)
        limit: Maximum number of logs to return (default: 100)
        timeout_seconds: Request timeout in seconds (default: 30)
        
    Returns:
        List of log entries as dictionaries
        
    Example:
        >>> logs = query_logs("service:sikdae-android status:error")
        >>> for log in logs:
        ...     print(log.get("message"))
    """
    cfg = DatadogConfig()
    
    if not cfg.api_key or not cfg.app_key:
        print("datadog.py: API key or App key missing; returning empty list")
        return []
    
    # 기본 시간 범위 설정 (1시간 전 ~ 현재)
    if to_time is None:
        to_time = datetime.utcnow()
    if from_time is None:
        from_time = to_time - timedelta(hours=1)
    
    # Datadog API 엔드포인트
    site = cfg.site
    api_endpoint = f"https://api.{site}/api/v2/logs/events/search"
    
    # 요청 본문 구성
    request_body = {
        "filter": {
            "query": query,
            "from": int(from_time.timestamp() * 1000),  # milliseconds
            "to": int(to_time.timestamp() * 1000),  # milliseconds
        },
        "page": {
            "limit": limit
        }
    }
    
    # JSON을 문자열로 변환하고 바이트로 인코딩
    request_data = json.dumps(request_body).encode("utf-8")
    
    # 재시도 로직
    max_attempts = 3
    
    for attempt in range(1, max_attempts + 1):
        try:
            # HTTP 요청 생성
            req = urllib.request.Request(
                api_endpoint,
                data=request_data,
                headers={
                    "Content-Type": "application/json",
                    "DD-API-KEY": cfg.api_key,
                    "DD-APPLICATION-KEY": cfg.app_key,
                },
                method="POST"
            )
            
            # API 호출
            with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                # 응답 읽기 및 JSON 파싱
                response_data = json.loads(resp.read().decode("utf-8"))
                
                # Datadog API 응답 구조 확인
                # 성공 시: {"data": [...], "meta": {...}}
                if "data" in response_data:
                    logs = response_data.get("data", [])
                    
                    # Process logs to decode gzip bodies if present
                    for log in logs:
                        _try_decode_gzip_body(log)
                        
                    if attempt > 1:
                        print(f"datadog.py: Logs queried successfully (attempt {attempt}), {len(logs)} logs")
                    else:
                        print(f"datadog.py: Logs queried successfully, {len(logs)} logs")
                    return logs
                else:
                    error_msg = response_data.get("errors", [{}])[0].get("detail", "Unknown error")
                    print(f"datadog.py: API error: {error_msg}")
                    return []
                    
        except urllib.error.HTTPError as e:
            # HTTP 에러
            error_body = ""
            try:
                error_body = e.read().decode("utf-8")
            except:
                pass
            
            # 429 (Too Many Requests)나 5xx 에러는 재시도
            is_retryable = e.code == 429 or e.code >= 500
            
            if is_retryable and attempt < max_attempts:
                retry_after = e.headers.get("Retry-After")
                wait_time = int(retry_after) if retry_after else attempt * 2
                print(f"datadog.py: HTTP error {e.code} (attempt {attempt}/{max_attempts})")
                print(f"datadog.py: Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            else:
                print(f"datadog.py: HTTP error {e.code}: {error_body[:200]}")
                return []
                
        except urllib.error.URLError as e:
            # 네트워크 오류
            if attempt < max_attempts:
                wait_time = attempt
                print(f"datadog.py: URL error (attempt {attempt}/{max_attempts}): {e}")
                print(f"datadog.py: Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            else:
                print(f"datadog.py: URL error: {e}")
                return []
                
        except Exception as exc:
            # 기타 예상치 못한 오류
            if attempt < max_attempts:
                wait_time = attempt
                print(f"datadog.py: Unexpected error (attempt {attempt}/{max_attempts}): {exc}")
                print(f"datadog.py: Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            else:
                print(f"datadog.py: Unexpected error: {exc}")
                return []
    
    # 모든 재시도 실패 시
    return []


def format_logs_for_analysis(logs: List[Dict]) -> str:
    """Format logs into a readable string for AI analysis.
    
    로그를 AI 분석에 적합한 형식으로 포맷팅합니다.
    효율성을 위해 핵심 정보만 포함하고 불필요한 중복 정보는 제거합니다.
    
    최적화 전략:
    - 중첩된 attributes 구조 지원
    - 타임스탬프는 시간만 표시 (날짜 생략)
    - 사용자/고객사 ID는 변경될 때만 표시 (중복 제거)
    - 각 로그 메시지는 최대 200자로 제한
    - 빈 메시지나 너무 짧은 메시지는 스킵
    
    Args:
        logs: List of log entries from Datadog
        
    Returns:
        Formatted string containing log messages with metadata
    """
    if not logs:
        return "로그가 없습니다."
    
    lines = []
    prev_user_id = None
    prev_customer_id = None
    
    for i, log in enumerate(logs, 1):
        attributes = log.get("attributes", {})
        nested_attrs = attributes.get("attributes", {})
        
        # 메시지 추출 (중첩 구조 고려)
        message = nested_attrs.get("message") or attributes.get("message") or log.get("message", "")
        
        # 타임스탬프: app-timestamp 우선, 없으면 timestamp 사용
        timestamp = (
            nested_attrs.get("app-timestamp") or 
            attributes.get("app-timestamp") or 
            attributes.get("timestamp") or 
            log.get("timestamp", "")
        )
        service = attributes.get("service", log.get("service", "unknown"))
        level = attributes.get("status") or nested_attrs.get("status") or attributes.get("level") or "info"
        
        # 사용자 및 고객사 정보 (CS 분석에 유용하지만 중복 제거)
        user_id = nested_attrs.get("ua-user-id") or attributes.get("ua-user-id", "")
        customer_id = nested_attrs.get("ua-com-id") or attributes.get("ua-com-id", "")
        
        # 추가 필드 추출 (AI 분석에 포함)
        device_model = nested_attrs.get("ua-device-model") or attributes.get("ua-device-model", "")
        app_version = nested_attrs.get("ua-device-cv") or attributes.get("ua-device-cv", "")
        ui_event = nested_attrs.get("ui-event") or attributes.get("ui-event", "")
        ui_screen = nested_attrs.get("ui-screen") or attributes.get("ui-screen", "")
        ui_args_raw = nested_attrs.get("ui-args") or attributes.get("ui-args", "")
        # ui-args가 딕셔너리인 경우 JSON 문자열로 변환
        if ui_args_raw and isinstance(ui_args_raw, dict):
            ui_args = json.dumps(ui_args_raw, ensure_ascii=False)
        elif ui_args_raw:
            ui_args = str(ui_args_raw)
        else:
            ui_args = ""
        
        # 타임스탬프 포맷팅 (간단한 형식 - 시간만 표시)
        if timestamp:
            try:
                if isinstance(timestamp, (int, float)):
                    if timestamp > 1e10:  # 밀리초
                        dt = datetime.fromtimestamp(timestamp / 1000)
                    else:  # 초
                        dt = datetime.fromtimestamp(timestamp)
                else:
                    dt = datetime.fromisoformat(str(timestamp).replace('Z', '+00:00'))
                timestamp_str = dt.strftime("%H:%M:%S")  # 시간만 표시 (날짜는 생략)
            except:
                timestamp_str = str(timestamp)[:19]  # 최대 19자로 제한
        else:
            timestamp_str = "N/A"
        
        # 로그 라인 구성 (더 간결하게)
        # 에러/경고만 레벨 표시, info는 생략
        if level.lower() in ["error", "warn", "warning", "critical", "fatal"]:
            log_parts = [f"[{i}]", timestamp_str, f"[{level}]"]
        else:
            log_parts = [f"[{i}]", timestamp_str]  # info 레벨은 생략
        
        # 사용자/고객사 정보는 변경될 때만 표시 (중복 제거, 더 짧게)
        if user_id and user_id != prev_user_id:
            log_parts.append(f"[u:{user_id[:6]}...]")  # 더 짧게
        if customer_id and customer_id != prev_customer_id:
            log_parts.append(f"[c:{customer_id[:6]}...]")
        
        # 추가 정보 추가 (AI 분석에 포함)
        metadata_parts = []
        if device_model:
            metadata_parts.append(f"device-model:{device_model}")
        if app_version:
            metadata_parts.append(f"app-version:{app_version}")
        if ui_event:
            metadata_parts.append(f"ui-event:{ui_event}")
        if ui_screen:
            metadata_parts.append(f"ui-screen:{ui_screen}")
        if ui_args:
            metadata_parts.append(f"ui-args:{ui_args}")
        
        # 메시지 처리: 없거나 짧으면 기본 메시지 생성
        if not message or len(message.strip()) < 3:
            # 메시지가 없어도 다른 정보(레벨, 서비스, UI 이벤트 등)를 표시
            http_uri = nested_attrs.get("http-request-uri") or attributes.get("http-request-uri", "")
            
            # 대체 메시지 생성
            message_parts = []
            if ui_event:
                message_parts.append(f"ui-event:{ui_event}")
            if ui_screen:
                message_parts.append(f"ui-screen:{ui_screen}")
            if ui_args:
                message_parts.append(f"ui-args:{ui_args}")
            if http_uri:
                message_parts.append(f"http-request-uri:{http_uri}")
            if service and service != "unknown":
                message_parts.append(f"service:{service}")
            
            if message_parts:
                message = " | ".join(message_parts)
            else:
                # 최소한의 정보라도 표시
                message = f"[{level}] 로그 (메시지 없음)"
        else:
            # 메시지 길이 제한 (각 로그당 최대 300자로 증가)
            if len(message) > 300:
                message = message[:297] + "..."
        
        # 메타데이터가 있으면 메시지에 추가
        if metadata_parts:
            message = f"{message} ({' | '.join(metadata_parts)})"
        
        log_parts.append(message)
        lines.append(" ".join(log_parts))
        
        # 이전 값 저장 (중복 체크용)
        prev_user_id = user_id
        prev_customer_id = customer_id
    
    # 모든 로그가 스킵된 경우 안내 메시지 반환
    if not lines:
        return "로그는 조회되었으나 표시할 메시지가 없습니다. (로그 구조 확인 필요)"
    
    return "\n".join(lines)
