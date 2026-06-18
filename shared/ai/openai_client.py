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

import logging
import time
from typing import Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # SDK가 설치되지 않은 경우를 대비

from core.config import OpenAIConfig

logger = logging.getLogger("ai.openai")


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
        model: OpenAI model to use (default: OPENAI_MODEL or "gpt-5.4").

    Returns:
        A summary string, or an error message if the API call fails.
    """

    cfg = OpenAIConfig()
    if not cfg.api_key:
        # Stubbed behavior: deterministic, helpful output for demos/tests.
        logger.warning("OPENAI_API_KEY 미설정 — 스텁 요약 반환")
        return f"{url} 요약 완료 (테스트)"

    # openai SDK가 설치되지 않은 경우
    if OpenAI is None:
        logger.warning("openai 패키지 미설치 — 'pip install openai' 필요")
        return f"{url} 요약 실패 (SDK 미설치)"

    # OpenAI API 클라이언트 초기화 (timeout 기본 15초)
    client = OpenAI(api_key=cfg.api_key, timeout=timeout_seconds)

    # 뉴스 요약 프롬프트 생성 (본문 우선, 없으면 title+description 기반)
    prompt = _build_news_prompt(
        url=url,
        title=title,
        description=description,
        article_text=article_text,
    )
    # 모델 선택 우선순위: 함수 인자 > 환경변수(OPENAI_MODEL) > 기본값
    model_name = model or getattr(cfg, "model", "") or "gpt-5.4"
    logger.debug("OpenAI 요약 요청: model=%s, prompt_len=%d", model_name, len(prompt))

    # 일시적 오류(timeout/503/overloaded/rate limit)에 대비해 지수 백오프로 재시도
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                timeout=timeout_seconds,
            )
            summary = response.choices[0].message.content.strip()
            logger.debug(
                "OpenAI 요약 성공: response_len=%d (attempt %d)", len(summary), attempt
            )
            return summary
        except Exception as exc:
            error_str = str(exc)
            error_type = type(exc).__name__
            lowered = error_str.lower()
            is_retryable = (
                "timeout" in lowered
                or "timed out" in lowered
                or "503" in error_str
                or "overloaded" in lowered
                or "unavailable" in lowered
                or "rate limit" in lowered
                or "try again" in lowered
            )
            if is_retryable and attempt < max_attempts:
                wait_time = 2 ** attempt  # 2초, 4초
                logger.warning(
                    "OpenAI 요약 실패(attempt %d/%d, %ds 후 재시도): %s: %s",
                    attempt, max_attempts, wait_time, error_type, error_str[:100],
                )
                time.sleep(wait_time)
                continue
            error_detail = f"{error_type}: {error_str[:100]}"
            logger.error("OpenAI 요약 최종 실패(attempt %d): %s", attempt, error_detail)
            return f"{url} 요약 실패 ({error_detail})"

    return f"{url} 요약 실패 (재시도 한계 도달)"
