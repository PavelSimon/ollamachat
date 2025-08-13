"""
Base API framework for v1 endpoints.

Provides common functionality for all v1 API endpoints including
request validation, response formatting, and error handling.
"""

from functools import wraps
from typing import Dict, Any, Optional, Callable
from flask import request, jsonify, g
import time
import uuid
from datetime import datetime

from error_handlers import ErrorHandler


def generate_request_id() -> str:
    """Generate a unique request ID for tracking."""
    return str(uuid.uuid4())


def api_response(data: Any = None, message: str = None, status_code: int = 200) -> tuple:
    """
    Standardized API response format for v1 endpoints.
    
    Args:
        data: Response data
        message: Optional message
        status_code: HTTP status code
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    response = {
        'success': 200 <= status_code < 300,
        'timestamp': datetime.utcnow().isoformat(),
        'request_id': getattr(g, 'request_id', None),
        'version': 'v1'
    }
    
    if data is not None:
        response['data'] = data
        
    if message:
        response['message'] = message
        
    return response, status_code


def api_error(error_type: str, message: str, details: Dict = None, status_code: int = 400) -> tuple:
    """
    Standardized API error response for v1 endpoints.
    
    Args:
        error_type: Type of error
        message: Error message
        details: Optional error details
        status_code: HTTP status code
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    response = {
        'success': False,
        'timestamp': datetime.utcnow().isoformat(),
        'request_id': getattr(g, 'request_id', None),
        'version': 'v1',
        'error': {
            'type': error_type,
            'message': message,
            'details': details or {}
        }
    }
    
    return response, status_code


def track_request():
    """
    Decorator to add request tracking to API endpoints.
    
    Adds request ID, timing, and basic request information to Flask's g object.
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Generate request ID and store in g
            g.request_id = generate_request_id()
            g.request_start_time = time.time()
            g.endpoint = f.__name__
            
            # Store request info for logging
            g.request_info = {
                'method': request.method,
                'path': request.path,
                'remote_addr': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', 'Unknown')
            }
            
            try:
                result = f(*args, **kwargs)
                
                # Add timing information
                g.request_duration = time.time() - g.request_start_time
                
                return result
                
            except Exception as e:
                # Log error and return standardized error response
                g.request_duration = time.time() - g.request_start_time
                return ErrorHandler.internal_error(
                    e,
                    f"API v1 endpoint: {f.__name__}",
                    "Internal server error occurred"
                )
                
        return wrapper
    return decorator


def validate_json():
    """
    Decorator to validate that request contains valid JSON.
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            if request.method in ['POST', 'PUT', 'PATCH']:
                if not request.is_json:
                    return api_error(
                        'validation_error',
                        'Request must contain valid JSON',
                        {'content_type': request.content_type},
                        400
                    )
                    
                # Validate JSON can be parsed
                try:
                    request.get_json()
                except Exception as e:
                    return api_error(
                        'validation_error',
                        'Invalid JSON in request body',
                        {'parse_error': str(e)},
                        400
                    )
            
            return f(*args, **kwargs)
            
        return wrapper
    return decorator


def require_fields(*required_fields):
    """
    Decorator to validate required fields in JSON request.
    
    Args:
        required_fields: List of required field names
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            if request.method in ['POST', 'PUT', 'PATCH']:
                data = request.get_json() or {}
                missing_fields = []
                
                for field in required_fields:
                    if field not in data or data[field] is None:
                        missing_fields.append(field)
                
                if missing_fields:
                    return api_error(
                        'validation_error',
                        'Missing required fields',
                        {'missing_fields': missing_fields},
                        400
                    )
            
            return f(*args, **kwargs)
            
        return wrapper
    return decorator


class APIRateLimiter:
    """
    Enhanced rate limiting for v1 API endpoints.
    """
    
    @staticmethod
    def apply_limits():
        """Apply appropriate rate limits based on endpoint type."""
        # This can be extended to apply different limits based on endpoint patterns
        # For now, we'll use the existing rate limiter
        pass