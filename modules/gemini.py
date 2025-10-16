"""
Purpose: Summarization service wrapper (Gemini placeholder).

Why: Provide a stable interface with timeout/retry scaffolding and
environment-based configuration, while remaining functional without
external calls during MVP.

How: If `GEMINI_API_KEY` is not set, return a deterministic stub so that
the flow remains testable. If the key exists, this module exposes a simple
retry loop shell where real HTTP calls can be added later without changing
the public function signature.
"""

from __future__ import annotations

import time
from typing import Optional

from .config import GeminiConfig


def get_summary_from_gemini(url: str, *, timeout_seconds: int = 15, max_retries: int = 2) -> str:
    """Return a short summary for the given URL.

    Behavior:
    - If no API key is configured, return a stubbed summary to keep the flow
      functional during early development.
    - If an API key exists, attempt a (future) provider call with basic retries.

    Note: The real HTTP call is intentionally omitted in MVP to avoid adding
    network dependencies. Insert HTTP client logic where marked.
    """

    cfg = GeminiConfig()
    if not cfg.api_key:
        # Stubbed behavior: deterministic, helpful output for demos/tests.
        print("gemini.py: API key missing; returning stub summary")
        return f"{url} 요약 완료 (테스트)"

    # Placeholder retry loop for future real integration.
    last_error: Optional[Exception] = None
    for attempt in range(1, max_retries + 2):  # e.g., retries=2 => up to 3 tries
        try:
            # TODO: Implement real HTTP call with standard library (urllib)
            # or an approved HTTP client. Respect `timeout_seconds`.
            # Example sketch (not active):
            #   req = urllib.request.Request(api_endpoint, ...)
            #   with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            #       data = json.load(resp)
            #       return data["summary"]

            # For now, return a pseudo-summary to prove the retry path is functional.
            print(f"gemini.py: simulated provider call (attempt {attempt})")
            return f"{url} 요약(가상 호출)"
        except Exception as exc:  # pragma: no cover - placeholder
            last_error = exc
            # Simple backoff (fixed). Can be replaced with exponential backoff later.
            time.sleep(0.25)

    # If all attempts fail, provide a graceful fallback rather than raising.
    print(f"gemini.py: provider call failed after retries: {last_error}")
    return f"{url} 요약 실패(임시)"


