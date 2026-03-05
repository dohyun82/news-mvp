"""
Purpose: Summarization service wrapper for OpenAI API.

Why: Provide a stable interface with timeout handling and
environment-based configuration, while remaining functional without
external calls during MVP.

How: If `OPENAI_API_KEY` is not set, return a deterministic stub so that
the flow remains testable. If the key exists, this module calls OpenAI API
to generate summaries using the official openai SDK.
"""

from __future__ import annotations

from typing import Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # SDK가 설치되지 않은 경우를 대비

from core.config import OpenAIConfig


def _build_news_prompt(
    *,
    url: str,
    title: Optional[str],
    description: Optional[str],
    article_text: Optional[str],
) -> str:
    title_text = (title or "").strip()
    description_text = (description or "").strip()
    article_body = (article_text or "").strip()

    sections = []
    sections.append("다음 입력 정보에 근거해서만 뉴스 요약을 작성해주세요.")
    sections.append("[규칙]")
    sections.append("1) 입력에 없는 사실을 추측하거나 단정하지 말 것.")
    sections.append("2) 숫자/날짜/주체가 불명확하면 '불명확'이라고 명시할 것.")
    sections.append("3) 3~5줄, 간결하고 사실 중심 문장으로 작성할 것.")
    sections.append("4) 광고성 표현이나 과장 표현은 제거할 것.")
    sections.append("")
    sections.append(f"[URL]\n{url}")
    if title_text:
        sections.append(f"[제목]\n{title_text}")
    if description_text:
        sections.append(f"[요약문(description)]\n{description_text}")
    if article_body:
        sections.append(f"[본문]\n{article_body}")
    sections.append("")
    sections.append("출력은 한국어 평문 요약만 작성해주세요.")
    return "\n".join(sections)


def get_summary_from_openai(
    url: str,
    *,
    title: Optional[str] = None,
    description: Optional[str] = None,
    article_text: Optional[str] = None,
    timeout_seconds: int = 15,
    model: Optional[str] = None,
) -> str:
    """Return a short summary for the given URL.

    Behavior:
    - If no API key is configured, return a stubbed summary to keep the flow
      functional during early development.
    - If an API key exists, call OpenAI API once to generate a summary.
    - No retry logic: API call is attempted only once (no retries on timeout or errors).

    Args:
        url: The URL of the news article to summarize.
        title: Optional article title to improve summary quality.
        description: Optional description text from crawler metadata.
        article_text: Optional full article body extracted from URL.
        timeout_seconds: HTTP request timeout in seconds (default: 15).
        model: OpenAI model to use (default: OPENAI_MODEL or "gpt-5.2").

    Returns:
        A summary string, or an error message if the API call fails.
    """

    cfg = OpenAIConfig()
    if not cfg.api_key:
        # Stubbed behavior: deterministic, helpful output for demos/tests.
        print("openai_client.py: API key missing; returning stub summary")
        return f"{url} 요약 완료 (테스트)"

    # openai SDK가 설치되지 않은 경우
    if OpenAI is None:
        print("openai_client.py: openai 패키지가 설치되지 않았습니다. 'pip install openai' 실행 필요")
        return f"{url} 요약 실패 (SDK 미설치)"

    # OpenAI API 클라이언트 초기화
    # timeout 설정: 기본값 15초를 사용하되, 더 긴 응답 시간이 필요한 경우를 대비
    client = OpenAI(api_key=cfg.api_key, timeout=timeout_seconds)
    
    # 프롬프트 준비
    # url이 "log_analysis"인 경우: title을 완성된 프롬프트로 간주 (로그 분석)
    # 그 외의 경우: 뉴스 요약용 프롬프트 추가
    if url == "log_analysis" and title:
        # 로그 분석: title이 이미 완성된 프롬프트
        prompt = title
    else:
        # 뉴스 요약: 본문(article_text) 우선, 없으면 title+description 기반
        prompt = _build_news_prompt(
            url=url,
            title=title,
            description=description,
            article_text=article_text,
        )
    
    # API 호출 (1번만 시도, 재시도 없음)
    try:
        # 모델 선택 우선순위: 함수 인자 > 환경변수(OPENAI_MODEL) > 하드코딩 기본값
        model_name = model or getattr(cfg, "model", "") or "gpt-5.2"
        
        # API 호출 전 로깅: 전송되는 데이터 기록
        print("=" * 80)
        print("OpenAI API 호출 - 전송 데이터")
        print("=" * 80)
        print(f"모델: {model_name}")
        print(f"타임아웃: {timeout_seconds}초")
        print(f"프롬프트 길이: {len(prompt)}자")
        print(f"프롬프트 내용 (처음 500자):")
        print("-" * 80)
        print(prompt[:500])
        if len(prompt) > 500:
            print(f"... (총 {len(prompt)}자, 나머지 {len(prompt) - 500}자 생략)")
        print("-" * 80)
        print(f"전체 프롬프트 길이: {len(prompt)}자")
        print("=" * 80)
        
        # OpenAI API 호출
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            timeout=timeout_seconds
        )
        
        # 응답에서 텍스트 추출
        summary = response.choices[0].message.content.strip()
        
        # API 호출 성공 로깅
        print("=" * 80)
        print("OpenAI API 호출 성공")
        print("=" * 80)
        print(f"응답 길이: {len(summary)}자")
        print(f"응답 내용 (처음 300자):")
        print("-" * 80)
        print(summary[:300])
        if len(summary) > 300:
            print(f"... (총 {len(summary)}자, 나머지 {len(summary) - 300}자 생략)")
        print("-" * 80)
        print("=" * 80)
        
        return summary
        
    except Exception as exc:
        # 에러 발생 시 즉시 실패 반환 (재시도 없음)
        error_str = str(exc)
        error_type = type(exc).__name__
        error_detail = f"{error_type}: {error_str[:100]}" if error_str else str(exc)
        
        # API 호출 실패 로깅
        print("=" * 80)
        print("OpenAI API 호출 실패")
        print("=" * 80)
        print(f"에러 타입: {error_type}")
        print(f"에러 메시지: {error_str}")
        print(f"전송했던 프롬프트 길이: {len(prompt)}자")
        print("=" * 80)
        
        return f"{url} 요약 실패 ({error_detail})"
