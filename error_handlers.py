"""
Standardized error handling for OLLAMA Chat application.

This module provides centralized error handling classes and utilities
to ensure consistent error responses across all API endpoints.
"""

from typing import Dict, Any, Optional, Tuple
from flask import jsonify, current_app
from marshmallow import ValidationError
from datetime import datetime
import traceback
import uuid


class ErrorType:
    """Standard error types for consistent error handling."""
    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    INTERNAL_ERROR = "internal_error"
    EXTERNAL_SERVICE_ERROR = "external_service_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    CONFIGURATION_ERROR = "configuration_error"


class StandardError:
    """Standard error response structure."""
    
    def __init__(
        self,
        error_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        status_code: int = 500
    ):
        self.error_type = error_type
        self.message = message
        self.details = details or {}
        self.user_message = user_message or message
        self.status_code = status_code
        self.error_id = str(uuid.uuid4())
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format."""
        return {
            "error": {
                "type": self.error_type,
                "message": self.message,
                "user_message": self.user_message,
                "details": self.details,
                "error_id": self.error_id,
                "timestamp": self.timestamp
            }
        }

    def to_response(self) -> Tuple[Dict[str, Any], int]:
        """Convert error to Flask response tuple."""
        return self.to_dict(), self.status_code


class ErrorHandler:
    """Centralized error handler for consistent error responses."""

    @staticmethod
    def validation_error(
        validation_error: ValidationError,
        user_message: str = "Neplatné údaje v požiadavke"
    ) -> Tuple[Dict[str, Any], int]:
        """Handle validation errors from Marshmallow."""
        error = StandardError(
            error_type=ErrorType.VALIDATION_ERROR,
            message="Validation failed",
            details={"validation_errors": validation_error.messages},
            user_message=user_message,
            status_code=400
        )
        
        current_app.logger.warning(
            f"Validation error [{error.error_id}]: {validation_error.messages}"
        )
        
        return error.to_response()

    @staticmethod
    def not_found(
        resource: str,
        user_message: Optional[str] = None
    ) -> Tuple[Dict[str, Any], int]:
        """Handle not found errors."""
        message = f"{resource} not found"
        user_message = user_message or f"{resource} nenájdený"
        
        error = StandardError(
            error_type=ErrorType.NOT_FOUND,
            message=message,
            user_message=user_message,
            status_code=404
        )
        
        current_app.logger.info(f"Not found [{error.error_id}]: {message}")
        
        return error.to_response()

    @staticmethod
    def unauthorized(
        user_message: str = "Neautorizovaný prístup"
    ) -> Tuple[Dict[str, Any], int]:
        """Handle unauthorized access errors."""
        error = StandardError(
            error_type=ErrorType.UNAUTHORIZED,
            message="Unauthorized access",
            user_message=user_message,
            status_code=401
        )
        
        current_app.logger.warning(f"Unauthorized access [{error.error_id}]")
        
        return error.to_response()

    @staticmethod
    def forbidden(
        user_message: str = "Nemáte oprávnenie na túto akciu"
    ) -> Tuple[Dict[str, Any], int]:
        """Handle forbidden access errors."""
        error = StandardError(
            error_type=ErrorType.FORBIDDEN,
            message="Access forbidden",
            user_message=user_message,
            status_code=403
        )
        
        current_app.logger.warning(f"Access forbidden [{error.error_id}]")
        
        return error.to_response()

    @staticmethod
    def external_service_error(
        service: str,
        original_error: Exception,
        user_message: Optional[str] = None
    ) -> Tuple[Dict[str, Any], int]:
        """Handle external service errors (e.g., OLLAMA connection issues)."""
        message = f"External service error: {service}"
        user_message = user_message or f"Chyba pri pripojení k {service}"
        
        error = StandardError(
            error_type=ErrorType.EXTERNAL_SERVICE_ERROR,
            message=message,
            details={
                "service": service,
                "original_error": str(original_error)
            },
            user_message=user_message,
            status_code=503
        )
        
        current_app.logger.error(
            f"External service error [{error.error_id}]: {service} - {str(original_error)}"
        )
        
        return error.to_response()

    @staticmethod
    def internal_error(
        original_error: Exception,
        context: str = "",
        user_message: str = "Vyskytla sa neočakávaná chyba"
    ) -> Tuple[Dict[str, Any], int]:
        """Handle internal server errors."""
        error = StandardError(
            error_type=ErrorType.INTERNAL_ERROR,
            message=f"Internal server error: {context}",
            details={
                "context": context,
                "original_error": str(original_error)
            },
            user_message=user_message,
            status_code=500
        )
        
        # Log full traceback for internal errors
        current_app.logger.error(
            f"Internal error [{error.error_id}]: {context}\n"
            f"Original error: {str(original_error)}\n"
            f"Traceback: {traceback.format_exc()}"
        )
        
        return error.to_response()

    @staticmethod
    def rate_limit_error(
        user_message: str = "Prekročený limit požiadaviek. Skúste neskôr."
    ) -> Tuple[Dict[str, Any], int]:
        """Handle rate limiting errors."""
        error = StandardError(
            error_type=ErrorType.RATE_LIMIT_ERROR,
            message="Rate limit exceeded",
            user_message=user_message,
            status_code=429
        )
        
        current_app.logger.warning(f"Rate limit exceeded [{error.error_id}]")
        
        return error.to_response()

    @staticmethod
    def configuration_error(
        config_item: str,
        user_message: str = "Chyba v konfigurácii aplikácie"
    ) -> Tuple[Dict[str, Any], int]:
        """Handle configuration errors."""
        error = StandardError(
            error_type=ErrorType.CONFIGURATION_ERROR,
            message=f"Configuration error: {config_item}",
            details={"config_item": config_item},
            user_message=user_message,
            status_code=500
        )
        
        current_app.logger.error(
            f"Configuration error [{error.error_id}]: {config_item}"
        )
        
        return error.to_response()


def create_validation_error_response(validation_error: ValidationError) -> Tuple[Dict[str, Any], int]:
    """
    Legacy function for backward compatibility.
    Use ErrorHandler.validation_error() for new code.
    """
    return ErrorHandler.validation_error(validation_error)


# Flask error handlers for global error handling
def register_error_handlers(app):
    """Register global error handlers with Flask app."""
    
    @app.errorhandler(404)
    def handle_404(error):
        return ErrorHandler.not_found("Stránka", "Stránka nenájdená")

    @app.errorhandler(500)
    def handle_500(error):
        return ErrorHandler.internal_error(
            Exception("Internal server error"),
            "Global error handler"
        )

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        return ErrorHandler.validation_error(error)