"""
Purpose: Common logging and error handling utilities for the Flask app.

Why: Centralize request logging and exception handling so that all APIs have
consistent diagnostics without duplicating code across modules.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from flask import Request, Response, g, jsonify, request


def configure_logging(level: int = logging.INFO) -> None:
    """Initialize root logging if not already configured.

    Avoids duplicate handler installation when reloaded.
    """

    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
    root.setLevel(level)


def register_http_logging(app) -> None:
    """Attach simple request/response logging hooks to the Flask app."""

    @app.before_request
    def _start_timer() -> None:  # type: ignore[override]
        g._start_time = time.perf_counter()

    @app.after_request
    def _log_response(resp: Response) -> Response:  # type: ignore[override]
        try:
            start = getattr(g, "_start_time", None)
            duration_ms = None
            if start is not None:
                duration_ms = int((time.perf_counter() - start) * 1000)
            logging.getLogger("http").info(
                "%s %s -> %s %sms",
                request.method,
                request.path,
                resp.status_code,
                duration_ms if duration_ms is not None else "-",
            )
        except Exception:
            # Logging must never break the response flow
            pass
        return resp


def register_error_handlers(app) -> None:
    """Register a generic JSON error handler for unexpected exceptions."""

    @app.errorhandler(404)
    def _handle_404(err):  # type: ignore[override]
        """404 에러는 JSON이 아닌 기본 Flask 404 처리"""
        from flask import abort
        abort(404)

    @app.errorhandler(Exception)
    def _handle_exception(err: Exception):  # type: ignore[override]
        # 404는 제외 (Flask 기본 처리 사용)
        from werkzeug.exceptions import NotFound
        if isinstance(err, NotFound):
            raise err
        
        logging.getLogger("errors").exception("Unhandled exception: %s", err)
        return (
            jsonify({
                "error": {
                    "type": err.__class__.__name__,
                    "message": str(err),
                }
            }),
            500,
        )


__all__ = [
    "configure_logging",
    "register_http_logging",
    "register_error_handlers",
]


