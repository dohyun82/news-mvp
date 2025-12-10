"""
Purpose: Datadog API integration for log analysis.

Why: Provide a unified interface to query Datadog logs for mobile app
server/client logs to support CS response automation.

How: Use Datadog API to query logs and retrieve relevant log entries
for analysis.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from core.config import DatadogConfig


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
        query: Datadog log query string (e.g., "service:mobile-app status:error")
        from_time: Start time for query (default: 1 hour ago)
        to_time: End time for query (default: now)
        limit: Maximum number of logs to return (default: 100)
        timeout_seconds: Request timeout in seconds (default: 30)
        
    Returns:
        List of log entries as dictionaries
        
    Example:
        >>> logs = query_logs("service:mobile-app status:error")
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
    
    Args:
        logs: List of log entries from Datadog
        
    Returns:
        Formatted string containing log messages
    """
    if not logs:
        return "로그가 없습니다."
    
    lines = []
    for i, log in enumerate(logs, 1):
        message = log.get("attributes", {}).get("message", log.get("message", ""))
        timestamp = log.get("attributes", {}).get("timestamp", log.get("timestamp", ""))
        service = log.get("attributes", {}).get("service", log.get("service", "unknown"))
        level = log.get("attributes", {}).get("level", log.get("level", "info"))
        
        # 타임스탬프 포맷팅
        if timestamp:
            try:
                dt = datetime.fromtimestamp(timestamp / 1000)
                timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                timestamp_str = str(timestamp)
        else:
            timestamp_str = "N/A"
        
        lines.append(f"[{i}] {timestamp_str} [{service}] [{level}] {message}")
    
    return "\n".join(lines)
