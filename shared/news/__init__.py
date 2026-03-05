"""
Utilities for retrieving and normalizing article content from news URLs.
"""

from .article_content_extractor import ExtractResult, extract_article_content

__all__ = [
    "ExtractResult",
    "extract_article_content",
]
