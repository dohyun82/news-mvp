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
import time
import urllib.error
import urllib.request
from typing import Dict, List

from .config import SlackConfig


def _group_by_category(articles: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    grouped: Dict[str, List[Dict[str, str]]] = {}
    for a in articles:
        cat = a.get("category", "읽을거리")
        grouped.setdefault(cat, []).append(a)
    return grouped


def format_slack_message(articles: List[Dict[str, str]]) -> str:
    """Create a simple Slack-formatted message preserving bold/emojis style."""
    if not articles:
        return "*오늘의 클리핑*\n\n선택된 기사가 없습니다."

    grouped = _group_by_category(articles)
    lines: List[str] = []
    lines.append(":newspaper: *오늘의 클리핑*\n")

    order = ["그룹사", "업계", "참고", "읽을거리"]
    for cat in order:
        items = grouped.get(cat, [])
        if not items:
            continue
        lines.append(f"*[{cat}]*")
        for art in items:
            title = art.get("title", "")
            url = art.get("url", "")
            summary = art.get("summary", "")
            # Slack basic mrkdwn: link format <url|text>
            link = f"<{url}|{title}>" if url and title else (title or url)
            snippet = f" — {summary}" if summary else ""
            lines.append(f"• {link}{snippet}")
        lines.append("")  # blank line between categories

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
            # HTTP 요청 생성
            req = urllib.request.Request(
                api_endpoint,
                data=request_data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {cfg.bot_token}",
                },
                method="POST"
            )
            
            # API 호출
            with urllib.request.urlopen(req, timeout=10) as resp:
                # 응답 읽기 및 JSON 파싱
                response_data = json.loads(resp.read().decode("utf-8"))
                
                # Slack API 응답 확인
                # 성공 시: {"ok": true, "ts": "...", "channel": "..."}
                # 실패 시: {"ok": false, "error": "error_code"}
                if response_data.get("ok"):
                    if attempt > 1:
                        print(f"slack.py: Message sent successfully (attempt {attempt})")
                    else:
                        print("slack.py: Message sent successfully")
                    return True, "슬랙 메시지 전송 완료"
                else:
                    error_code = response_data.get("error", "unknown_error")
                    error_msg = f"Slack API error: {error_code}"
                    
                    # 재시도 가능한 에러인지 확인
                    # rate_limited: 429 에러, server_error: 5xx 에러
                    is_retryable = (
                        error_code == "rate_limited" or
                        "server_error" in error_code or
                        "internal_error" in error_code
                    )
                    
                    if is_retryable and attempt < max_attempts:
                        # rate_limited인 경우 응답 헤더에서 Retry-After 확인
                        retry_after = resp.headers.get("Retry-After")
                        wait_time = int(retry_after) if retry_after else attempt
                        print(f"slack.py: API call failed (attempt {attempt}/{max_attempts}): {error_msg}")
                        print(f"slack.py: Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        # 재시도 불가능한 에러
                        print(f"slack.py: API call failed: {error_msg}")
                        return False, f"슬랙 메시지 전송 실패: {error_code}"
                        
        except urllib.error.HTTPError as e:
            # HTTP 에러 (429, 5xx 등)
            error_body = ""
            try:
                error_body = e.read().decode("utf-8")
            except:
                pass
            
            # 429 (Too Many Requests)나 5xx 에러는 재시도
            is_retryable = e.code == 429 or e.code >= 500
            
            if is_retryable and attempt < max_attempts:
                # 429인 경우 Retry-After 헤더 확인
                retry_after = e.headers.get("Retry-After")
                wait_time = int(retry_after) if retry_after else attempt
                print(f"slack.py: HTTP error {e.code} (attempt {attempt}/{max_attempts})")
                print(f"slack.py: Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            else:
                print(f"slack.py: HTTP error {e.code}: {error_body[:200]}")
                return False, f"슬랙 메시지 전송 실패 (HTTP {e.code})"
                
        except urllib.error.URLError as e:
            # 네트워크 오류
            if attempt < max_attempts:
                wait_time = attempt
                print(f"slack.py: URL error (attempt {attempt}/{max_attempts}): {e}")
                print(f"slack.py: Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            else:
                print(f"slack.py: URL error: {e}")
                return False, f"슬랙 메시지 전송 실패 (네트워크 오류)"
                
        except Exception as exc:
            # 기타 예상치 못한 오류
            if attempt < max_attempts:
                wait_time = attempt
                print(f"slack.py: Unexpected error (attempt {attempt}/{max_attempts}): {exc}")
                print(f"slack.py: Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            else:
                print(f"slack.py: Unexpected error: {exc}")
                return False, f"슬랙 메시지 전송 실패 (예상치 못한 오류)"
    
    # 모든 재시도 실패 시
    return False, "슬랙 메시지 전송 실패 (재시도 한계 도달)"


