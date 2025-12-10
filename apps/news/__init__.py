"""
News clipping application module.

This module provides news collection, curation, summarization, and Slack delivery
functionality.
"""

from flask import Blueprint

news_bp = Blueprint('news', __name__, url_prefix='/news', template_folder='templates')

from . import routes
