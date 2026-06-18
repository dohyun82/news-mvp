"""
Purpose: Slack message formatting and (stub) delivery service.

Why: Keep Slack-specific formatting in one place and allow the app to work
even without real credentials in the MVP phase.

How: Build a category-grouped message. If Slack tokens are missing, return
the formatted preview instead of calling the API. Real HTTP integration can
be added later without changing the public function signature.
"""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from typing import Dict, List

from core.config import SlackConfig

logger = logging.getLogger("integrations.slack")


def _group_by_category(articles: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    grouped: Dict[str, List[Dict[str, str]]] = {}
    for a in articles:
        cat = a.get("category", "읽을거리")
        grouped.setdefault(cat, []).append(a)
    return grouped


def format_slack_message(articles: List[Dict[str, str]]) -> str:
    """Create a Slack-formatted message in Daily News Clipping style.
    
    Format:
    - Title: "Daily News Clipping" with checkmark icon
    - Categories with icons:
      - 그룹사: bulb icon
      - 업계: cloud icon
      - 참고: speech_balloon icon
      - 읽을거리: newspaper icon
    - Each article: bullet point with title and summary
    """
    if not articles:
        return ":white_check_mark: *Daily News Clipping*\n\n선택된 기사가 없습니다."

    grouped = _group_by_category(articles)
    lines: List[str] = []
    lines.append(":white_check_mark: *Daily News Clipping*\n")

    # 카테고리별 아이콘 매핑
    category_icons = {
        "그룹사": ":bulb:",
        "업계": ":cloud:",
        "참고": ":speech_balloon:",
        "읽을거리": ":newspaper:",
    }
    
    order = ["그룹사", "업계", "참고", "읽을거리"]
    for cat in order:
        items = grouped.get(cat, [])
        if not items:
            continue
        
        # 카테고리 헤더 (아이콘 + 카테고리명)
        icon = category_icons.get(cat, ":newspaper:")
        lines.append(f"{icon} *{cat} 뉴스*")
        
        # 각 기사 표시
        for art in items:
            title = art.get("title", "")
            url = art.get("url", "")
            summary = (art.get("summary") or "").strip()
            description = (art.get("description") or "").strip()
            detail_text = summary or description

            # 요약이 없으면 description을 대체 텍스트로 사용
            if detail_text:
                if url and title:
                    link = f"<{url}|{title}>"
                    lines.append(f"• {link}")
                    lines.append(f"  {detail_text}")
                else:
                    lines.append(f"• {title or url}")
                    lines.append(f"  {detail_text}")
            else:
                # 요약/description이 모두 없으면 제목만 링크로 표시
                if url and title:
                    link = f"<{url}|{title}>"
                    lines.append(f"• {link}")
                else:
                    lines.append(f"• {title or url}")
        
        lines.append("")  # 카테고리 간 빈 줄

    return "\n".join(lines).strip()


def send_message_to_slack(articles: List[Dict[str, str]]):
    """Send message to Slack or return a preview when credentials are missing.

    Returns:
        (success: bool, message: str) - message is either the provider result or
        a preview explanation during MVP.
    """

    cfg = SlackConfig()
    text = format_slack_message(articles)

    if not cfg.bot_token or not cfg.channel_id:
        # Preview path for MVP when secrets are not configured.
        preview = (text[:800] + "…") if len(text) > 800 else text
        return True, f"(미설정/프리뷰) 아래 메시지를 전송 예정:\n\n{preview}"

    # Slack Web API 엔드포인트
    api_endpoint = "https://slack.com/api/chat.postMessage"
    
    # 요청 본문 구성
    request_body = {
        "channel": cfg.channel_id,
        "text": text,
    }
    
    # JSON을 문자열로 변환하고 바이트로 인코딩
    request_data = json.dumps(request_body).encode("utf-8")
    
    # 재시도 로직: 일시적인 서버 오류에 대비하여 최대 3번 시도
    max_attempts = 3

    for attempt in range(1, max_attempts + 1):
        try:
            req = urllib.request.Request(
                api_endpoint,
                data=request_data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {cfg.bot_token}",
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=10) as resp:
                response_data = json.loads(resp.read().decode("utf-8"))

                # 성공: {"ok": true, ...} / 실패: {"ok": false, "error": ...}
                if response_data.get("ok"):
                    logger.info("슬랙 메시지 전송 완료 (attempt %d)", attempt)
                    return True, "슬랙 메시지 전송 완료"

                error_code = response_data.get("error", "unknown_error")
                # rate_limited(429)/server_error(5xx)는 재시도
                is_retryable = (
                    error_code == "rate_limited"
                    or "server_error" in error_code
                    or "internal_error" in error_code
                )
                if is_retryable and attempt < max_attempts:
                    retry_after = resp.headers.get("Retry-After")
                    wait_time = int(retry_after) if retry_after else attempt
                    logger.warning(
                        "슬랙 API 오류(attempt %d/%d, %ds 후 재시도): %s",
                        attempt, max_attempts, wait_time, error_code,
                    )
                    time.sleep(wait_time)
                    continue
                logger.error("슬랙 API 오류: %s", error_code)
                return False, f"슬랙 메시지 전송 실패: {error_code}"

        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode("utf-8")
            except Exception:
                pass

            is_retryable = e.code == 429 or e.code >= 500
            if is_retryable and attempt < max_attempts:
                retry_after = e.headers.get("Retry-After")
                wait_time = int(retry_after) if retry_after else attempt
                logger.warning(
                    "슬랙 HTTP 오류 %d (attempt %d/%d, %ds 후 재시도)",
                    e.code, attempt, max_attempts, wait_time,
                )
                time.sleep(wait_time)
                continue
            logger.error("슬랙 HTTP 오류 %d: %s", e.code, error_body[:200])
            return False, f"슬랙 메시지 전송 실패 (HTTP {e.code})"

        except urllib.error.URLError as e:
            if attempt < max_attempts:
                wait_time = attempt
                logger.warning(
                    "슬랙 네트워크 오류(attempt %d/%d, %ds 후 재시도): %s",
                    attempt, max_attempts, wait_time, e,
                )
                time.sleep(wait_time)
                continue
            logger.error("슬랙 네트워크 오류: %s", e)
            return False, "슬랙 메시지 전송 실패 (네트워크 오류)"

        except Exception as exc:
            if attempt < max_attempts:
                wait_time = attempt
                logger.warning(
                    "슬랙 전송 예외(attempt %d/%d, %ds 후 재시도): %s",
                    attempt, max_attempts, wait_time, exc,
                )
                time.sleep(wait_time)
                continue
            logger.error("슬랙 전송 예외: %s", exc)
            return False, "슬랙 메시지 전송 실패 (예상치 못한 오류)"

    # 모든 재시도 실패 시
    return False, "슬랙 메시지 전송 실패 (재시도 한계 도달)"
