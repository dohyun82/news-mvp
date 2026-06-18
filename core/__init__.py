"""
Core module for vendys-ai-automation-platform.

This module contains common utilities, configuration, and infrastructure
components shared across all applications.
"""

from .config import OpenAIConfig, RealDataConfig, SlackConfig
from .common import configure_logging, register_error_handlers, register_http_logging

__all__ = [
    "OpenAIConfig",
    "RealDataConfig",
    "SlackConfig",
    "configure_logging",
    "register_error_handlers",
    "register_http_logging",
]
