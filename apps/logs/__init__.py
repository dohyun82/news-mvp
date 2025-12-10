"""
Log analysis application module.

This module provides Datadog log analysis functionality for CS response automation.
"""

from flask import Blueprint

logs_bp = Blueprint('logs', __name__, url_prefix='/logs', template_folder='templates')

from . import routes
