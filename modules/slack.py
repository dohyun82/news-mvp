"""
Purpose: Slack message formatting and (stub) delivery service.

Why: Keep Slack-specific formatting in one place and allow the app to work
even without real credentials in the MVP phase.

How: Build a category-grouped message. If Slack tokens are missing, return
the formatted preview instead of calling the API. Real HTTP integration can
be added later without changing the public function signature.
"""

from __future__ import annotations

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

    # TODO: Implement Slack Web API call (chat.postMessage) using stdlib urllib
    #       to avoid new dependencies. Respect rate limits and errors.
    # For now, simulate success to keep flow working.
    print("slack.py: simulated Slack send (credentials detected)")
    return True, "슬랙 메시지 전송 완료(시뮬레이션)"


