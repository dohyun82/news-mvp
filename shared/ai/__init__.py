"""
AI client modules for vendys-ai-automation-platform.

Provides abstraction layer for AI model interactions, currently supporting OpenAI.
"""

from .base_client import BaseAIClient
from .openai_client import get_summary_from_openai

__all__ = [
    "BaseAIClient",
    "get_summary_from_openai",
]
