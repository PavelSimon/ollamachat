"""
Rate limiting utilities for OLLAMA Chat
Provides decorators and configuration for API endpoint rate limiting
"""

from functools import wraps
from flask import current_app, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


def get_limiter():
    """Get the rate limiter instance from the current app"""
    return current_app.extensions.get('limiter')


def rate_limit(limit_string):
    """
    Decorator to apply rate limiting to specific endpoints
    
    Args:
        limit_string: Rate limit specification (e.g., "5 per minute", "100 per hour")
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            limiter = get_limiter()
            if limiter:
                # Apply the rate limit
                try:
                    limiter.limit(limit_string)(f)(*args, **kwargs)
                except Exception as e:
                    # If rate limiting fails, log but don't break the request
                    current_app.logger.warning(f"Rate limiting error: {e}")
                    return f(*args, **kwargs)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def api_rate_limit(limit_string):
    """
    Specific rate limiting decorator for API endpoints
    Returns proper JSON error responses for rate limit exceeded
    
    Args:
        limit_string: Rate limit specification (e.g., "10 per minute")
    """
    def decorator(f):
        # Use Flask-Limiter's built-in decorator with custom error handler
        limiter = get_limiter()
        if limiter:
            return limiter.limit(limit_string)(f)
        return f
    return decorator


# Pre-defined rate limits for different endpoint types
class RateLimits:
    """Common rate limit configurations"""
    
    # Authentication endpoints
    LOGIN = "5 per minute"
    REGISTER = "3 per minute"
    
    # Chat management
    CHAT_CREATE = "10 per minute"
    CHAT_UPDATE = "20 per minute"
    CHAT_DELETE = "5 per minute"
    
    # Message sending (most restrictive)
    MESSAGE_SEND = "20 per minute"
    
    # API queries
    API_MODELS = "30 per minute"
    API_CONNECTION_TEST = "10 per minute"
    
    # Settings
    SETTINGS_UPDATE = "10 per minute"