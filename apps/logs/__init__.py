"""
Log analysis application module.

This module provides Datadog log analysis functionality for CS response automation.
"""

from flask import Blueprint
from pathlib import Path

# Blueprint의 템플릿 폴더를 명시적으로 지정
_template_folder = Path(__file__).parent / 'templates'
logs_bp = Blueprint('logs', __name__, url_prefix='/logs', template_folder=str(_template_folder))

from . import routes
