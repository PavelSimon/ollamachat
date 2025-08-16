"""
Input validation schemas for OLLAMA Chat API endpoints
Using marshmallow for consistent validation across all endpoints
"""

from marshmallow import Schema, fields, validate, ValidationError, post_load
from typing import Dict, Any


class ChatCreateSchema(Schema):
    """Schema for chat creation requests"""
    title = fields.Str(
        required=False, 
        allow_none=True, 
        validate=validate.Length(max=200),
        load_default=None
    )

    @post_load
    def clean_title(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Clean and validate title"""
        if data.get('title'):
            data['title'] = data['title'].strip()
            if not data['title']:
                data['title'] = None
        return data


class ChatUpdateSchema(Schema):
    """Schema for chat title updates"""
    title = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=200)
    )

    @post_load
    def clean_title(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Clean title"""
        data['title'] = data['title'].strip()
        if not data['title']:
            raise ValidationError("Title cannot be empty")
        return data


class MessageCreateSchema(Schema):
    """Schema for message creation requests"""
    chat_id = fields.Int(
        required=True,
        validate=validate.Range(min=1)
    )
    message = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=10000)
    )
    model = fields.Str(
        required=False,
        validate=validate.Length(max=100),
        load_default='gpt-oss:20b'
    )
    use_internet_search = fields.Bool(
        required=False,
        load_default=False
    )

    @post_load
    def clean_message(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Clean message content"""
        data['message'] = data['message'].strip()
        if not data['message']:
            raise ValidationError("Message cannot be empty")
        return data


class SettingsUpdateSchema(Schema):
    """Schema for user settings updates"""
    ollama_host = fields.Url(
        required=True,
        validate=validate.Length(max=255)
    )

    @post_load
    def clean_host(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Clean OLLAMA host URL"""
        data['ollama_host'] = data['ollama_host'].strip()
        if not data['ollama_host'].startswith(('http://', 'https://')):
            raise ValidationError("OLLAMA host must start with http:// or https://")
        return data


def validate_request_data(schema_class: Schema, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate request data against schema
    
    Args:
        schema_class: Marshmallow schema class to use for validation
        data: Request data to validate
        
    Returns:
        Validated and cleaned data
        
    Raises:
        ValidationError: If validation fails
    """
    schema = schema_class()
    try:
        return schema.load(data)
    except ValidationError as e:
        # Convert marshmallow errors to a more user-friendly format
        error_messages = []
        for field, messages in e.messages.items():
            for message in messages if isinstance(messages, list) else [messages]:
                error_messages.append(f"{field}: {message}")
        raise ValidationError("; ".join(error_messages))


def create_validation_error_response(error: ValidationError) -> tuple:
    """
    Create standardized error response for validation errors
    
    Args:
        error: Marshmallow ValidationError
        
    Returns:
        Tuple of (json_response, status_code)
    """
    return {
        'error': 'Validation failed',
        'details': str(error) if isinstance(error, ValidationError) else str(error.messages) if hasattr(error, 'messages') else str(error)
    }, 400