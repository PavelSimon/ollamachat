"""
API Version 1.

This module contains all v1 API endpoints with enhanced features
including proper versioning, documentation, and monitoring.
"""

from flask import Blueprint

# Create the v1 API blueprint
api_v1_bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')

# Import all v1 endpoints
from . import chat
from . import models  
from . import system
from . import users
from . import docs