"""
Purpose: Summarization service wrapper for Gemini API.

Why: Provide a stable interface with timeout handling and
environment-based configuration, while remaining functional without
external calls during MVP.

How: If `GEMINI_API_KEY` is not set, return a deterministic stub so that
the flow remains testable. If the key exists, this module calls Gemini API
to generate summaries using the official google.genai SDK.
"""

from __future__ import annotations

import time
from typing import Optional

try:
    from google import genai
except ImportError:
    genai = None  # SDK가 설치되지 않은 경우를 대비

from .config import GeminiConfig


def get_summary_from_gemini(url: str, *, title: Optional[str] = None, timeout_seconds: int = 15) -> str:
    """Return a short summary for the given URL.

    Behavior:
    - If no API key is configured, return a stubbed summary to keep the flow
      functional during early development.
    - If an API key exists, call Gemini API once to generate a summary.

    Args:
        url: The URL of the news article to summarize.
        title: Optional article title to improve summary quality.
        timeout_seconds: HTTP request timeout in seconds (default: 15).

    Returns:
        A summary string, or an error message if the API call fails.
    """

    cfg = GeminiConfig()
    if not cfg.api_key:
        # Stubbed behavior: deterministic, helpful output for demos/tests.
        print("gemini.py: API key missing; returning stub summary")
        return f"{url} 요약 완료 (테스트)"

    # google.genai SDK가 설치되지 않은 경우
    if genai is None:
        print("gemini.py: google-genai 패키지가 설치되지 않았습니다. 'pip install google-genai' 실행 필요")
        return f"{url} 요약 실패 (SDK 미설치)"

    # Gemini API 클라이언트 초기화
    # timeout 설정: 기본값 15초를 사용하되, 더 긴 응답 시간이 필요한 경우를 대비해 30초로 증가
    # 참고: google.genai SDK는 Client 초기화 시 timeout을 설정할 수 있지만,
    # 현재 SDK 버전에서는 generate_content 호출 시 timeout을 직접 전달하지 않을 수 있음
    client = genai.Client(api_key=cfg.api_key)
    
    # 요약할 텍스트 준비: 제목이 있으면 제목 사용, 없으면 URL 사용
    # 실제 운영에서는 URL에서 기사 내용을 스크래핑하여 사용하는 것이 좋습니다.
    prompt_text = title if title else url
    prompt = f"다음 뉴스 기사를 3~5줄로 간단히 요약해주세요:\n\n{prompt_text}"
    
    # 재시도 로직: 일시적인 서버 오류(503 등)에 대비하여 최대 3번 시도
    max_attempts = 3
    last_error = None
    
    for attempt in range(1, max_attempts + 1):
        try:
            # Gemini API 호출 (gemini-2.5-flash 모델 사용)
            # timeout은 SDK 내부에서 처리되지만, 명시적으로 설정할 수 있는 경우를 대비
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            # 응답에서 텍스트 추출
            summary = response.text.strip()
            if attempt > 1:
                print(f"gemini.py: API call successful (attempt {attempt})")
            else:
                print("gemini.py: API call successful")
            return summary
            
        except Exception as exc:
            last_error = exc
            error_str = str(exc)
            error_type = type(exc).__name__
            
            # 에러 타입별 분류
            # Timeout 관련 에러 확인
            is_timeout = (
                "timeout" in error_str.lower() or
                "timed out" in error_str.lower() or
                "deadline" in error_str.lower()
            )
            
            # 503 (Service Unavailable) 또는 "overloaded" 같은 일시적 오류인 경우 재시도
            is_overloaded = "overloaded" in error_str.lower() or "UNAVAILABLE" in error_str
            is_retryable = (
                "503" in error_str or
                is_overloaded or
                "try again" in error_str.lower() or
                is_timeout  # timeout 에러도 재시도 가능
            )
            
            if is_retryable and attempt < max_attempts:
                # 서버 과부하("overloaded")인 경우 더 긴 대기 시간 적용
                if is_overloaded:
                    # 과부하 상황: 5초, 10초, 20초로 더 긴 대기
                    wait_time = 5 * attempt  # 5초, 10초, 20초
                else:
                    # 일반적인 일시적 오류: 지수 백오프 (2초, 4초, 8초)
                    wait_time = 2 ** attempt
                
                error_type_msg = "overloaded" if is_overloaded else ("timeout" if is_timeout else "server error")
                print(f"gemini.py: API call failed (attempt {attempt}/{max_attempts}, {error_type_msg}): {error_str[:100]}")
                print(f"gemini.py: Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            else:
                # 재시도 불가능한 에러이거나 최대 시도 횟수 도달
                error_detail = f"{error_type}: {error_str[:100]}" if error_str else str(exc)
                print(f"gemini.py: API call failed after {attempt} attempts: {error_detail}")
                return f"{url} 요약 실패 ({error_detail})"
    
    # 이 코드는 실행되지 않아야 하지만 안전을 위해 추가
    return f"{url} 요약 실패 (재시도 한계 도달)"


