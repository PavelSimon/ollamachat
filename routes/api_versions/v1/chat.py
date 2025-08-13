"""
API v1 - Chat endpoints.

Enhanced chat management with improved features like batch operations,
advanced filtering, and export capabilities.
"""

from flask import jsonify, request
from flask_login import login_required, current_user
from marshmallow import ValidationError
import json
from datetime import datetime
from typing import List, Dict

from database_operations import ChatOperations, MessageOperations
from validation_schemas import ChatCreateSchema, MessageCreateSchema, validate_request_data
from error_handlers import ErrorHandler

from . import api_v1_bp
from .base import track_request, api_response, api_error, validate_json, require_fields


@api_v1_bp.route('/chats')
@login_required
@track_request()
def get_chats():
    """
    Get user's chats with enhanced filtering and pagination.
    
    Query Parameters:
        - limit: Number of chats to return (default: 50, max: 100)
        - offset: Number of chats to skip (default: 0)
        - search: Search term for chat titles
        - sort: Sort field (created_at, updated_at, title)
        - order: Sort order (asc, desc) (default: desc)
    """
    try:
        # Parse query parameters
        limit = min(int(request.args.get('limit', 50)), 100)
        offset = int(request.args.get('offset', 0))
        search = request.args.get('search', '').strip()
        sort_field = request.args.get('sort', 'updated_at')
        sort_order = request.args.get('order', 'desc')
        
        # Validate sort parameters
        valid_sort_fields = ['created_at', 'updated_at', 'title']
        if sort_field not in valid_sort_fields:
            return api_error(
                'validation_error',
                f'Invalid sort field: {sort_field}',
                {'valid_fields': valid_sort_fields},
                400
            )
        
        if sort_order not in ['asc', 'desc']:
            return api_error(
                'validation_error',
                f'Invalid sort order: {sort_order}',
                {'valid_orders': ['asc', 'desc']},
                400
            )
        
        # Get chats from database
        # Note: This would need enhancement to the ChatOperations class
        # For now, we'll use the existing method and apply filtering in Python
        all_chats = ChatOperations.get_user_chats(current_user.id)
        
        # Apply search filter
        if search:
            filtered_chats = [
                chat for chat in all_chats 
                if search.lower() in chat.title.lower()
            ]
        else:
            filtered_chats = all_chats
        
        # Apply sorting
        reverse = (sort_order == 'desc')
        if sort_field == 'title':
            filtered_chats.sort(key=lambda x: x.title.lower(), reverse=reverse)
        elif sort_field == 'created_at':
            filtered_chats.sort(key=lambda x: x.created_at, reverse=reverse)
        else:  # updated_at
            filtered_chats.sort(key=lambda x: x.updated_at, reverse=reverse)
        
        # Apply pagination
        total_count = len(filtered_chats)
        paginated_chats = filtered_chats[offset:offset + limit]
        
        # Format response
        chats_data = []
        for chat in paginated_chats:
            # Get message count for each chat
            messages = MessageOperations.get_chat_messages(chat.id, current_user.id)
            
            chat_data = {
                'id': chat.id,
                'title': chat.title,
                'created_at': chat.created_at.isoformat(),
                'updated_at': chat.updated_at.isoformat(),
                'message_count': len(messages),
                'preview': messages[-1].content[:100] + '...' if messages else None,
                'last_message_at': messages[-1].created_at.isoformat() if messages else None
            }
            chats_data.append(chat_data)
        
        response_data = {
            'chats': chats_data,
            'pagination': {
                'total_count': total_count,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + limit) < total_count
            },
            'filters': {
                'search': search,
                'sort': sort_field,
                'order': sort_order
            }
        }
        
        return api_response(
            data=response_data,
            message=f"Retrieved {len(chats_data)} chats"
        )
        
    except ValueError as e:
        return api_error(
            'validation_error',
            'Invalid query parameters',
            {'error': str(e)},
            400
        )
    except Exception as e:
        return ErrorHandler.internal_error(
            e,
            "getting user chats in v1 API",
            "Failed to retrieve chats"
        )


@api_v1_bp.route('/chats', methods=['POST'])
@login_required
@track_request()
@validate_json()
def create_chat():
    """
    Create a new chat with enhanced validation.
    
    Request Body:
        - title (optional): Custom chat title
        - initial_message (optional): First message for the chat
        - model (optional): Default model for the chat
    """
    try:
        data = request.get_json() or {}
        
        # Validate using existing schema
        schema = ChatCreateSchema()
        validated_data = validate_request_data(schema, data)
        
        # Create the chat
        chat = ChatOperations.create_chat(
            user_id=current_user.id,
            title=validated_data.get('title')
        )
        
        # Add initial message if provided
        initial_message = data.get('initial_message')
        if initial_message:
            MessageOperations.add_message(
                chat_id=chat.id,
                content=initial_message,
                is_user=True,
                model_name=data.get('model', 'user')
            )
        
        # Format response
        chat_data = {
            'id': chat.id,
            'title': chat.title,
            'created_at': chat.created_at.isoformat(),
            'updated_at': chat.updated_at.isoformat(),
            'message_count': 1 if initial_message else 0,
            'model': data.get('model')
        }
        
        return api_response(
            data={'chat': chat_data},
            message="Chat created successfully",
            status_code=201
        )
        
    except ValidationError as e:
        return ErrorHandler.validation_error(e, "Invalid chat data")
    except Exception as e:
        return ErrorHandler.internal_error(
            e,
            "creating chat in v1 API",
            "Failed to create chat"
        )


@api_v1_bp.route('/chats/<int:chat_id>')
@login_required
@track_request()
def get_chat_details(chat_id: int):
    """
    Get detailed information about a specific chat.
    
    Includes messages, metadata, and statistics.
    """
    try:
        # Verify chat ownership
        chat = ChatOperations.get_chat_by_id(chat_id, current_user.id)
        if not chat:
            return api_error(
                'not_found',
                f'Chat {chat_id} not found or access denied',
                {'chat_id': chat_id},
                404
            )
        
        # Get messages
        messages = MessageOperations.get_chat_messages(chat_id, current_user.id)
        
        # Format messages
        messages_data = []
        for msg in messages:
            message_data = {
                'id': msg.id,
                'content': msg.content,
                'is_user': msg.is_user,
                'model_name': msg.model_name,
                'created_at': msg.created_at.isoformat(),
                'word_count': len(msg.content.split()) if msg.content else 0
            }
            messages_data.append(message_data)
        
        # Calculate statistics
        user_messages = [m for m in messages if m.is_user]
        ai_messages = [m for m in messages if not m.is_user]
        
        statistics = {
            'total_messages': len(messages),
            'user_messages': len(user_messages),
            'ai_messages': len(ai_messages),
            'total_words': sum(len(m.content.split()) for m in messages if m.content),
            'models_used': list(set(m.model_name for m in messages if m.model_name and not m.is_user))
        }
        
        # Format response
        chat_data = {
            'id': chat.id,
            'title': chat.title,
            'created_at': chat.created_at.isoformat(),
            'updated_at': chat.updated_at.isoformat(),
            'messages': messages_data,
            'statistics': statistics
        }
        
        return api_response(
            data={'chat': chat_data},
            message=f"Chat details for '{chat.title}'"
        )
        
    except Exception as e:
        return ErrorHandler.internal_error(
            e,
            f"getting chat details for {chat_id}",
            "Failed to get chat details"
        )


@api_v1_bp.route('/chats/<int:chat_id>/export')
@login_required
@track_request()
def export_chat(chat_id: int):
    """
    Export chat in various formats.
    
    Query Parameters:
        - format: Export format (json, markdown, text) (default: json)
        - include_metadata: Include metadata in export (default: true)
    """
    try:
        export_format = request.args.get('format', 'json').lower()
        include_metadata = request.args.get('include_metadata', 'true').lower() == 'true'
        
        if export_format not in ['json', 'markdown', 'text']:
            return api_error(
                'validation_error',
                f'Invalid export format: {export_format}',
                {'valid_formats': ['json', 'markdown', 'text']},
                400
            )
        
        # Verify chat ownership
        chat = ChatOperations.get_chat_by_id(chat_id, current_user.id)
        if not chat:
            return api_error(
                'not_found',
                f'Chat {chat_id} not found or access denied',
                {'chat_id': chat_id},
                404
            )
        
        # Get messages
        messages = MessageOperations.get_chat_messages(chat_id, current_user.id)
        
        # Generate export based on format
        if export_format == 'json':
            export_data = _export_chat_json(chat, messages, include_metadata)
            content_type = 'application/json'
        elif export_format == 'markdown':
            export_data = _export_chat_markdown(chat, messages, include_metadata)
            content_type = 'text/markdown'
        else:  # text
            export_data = _export_chat_text(chat, messages, include_metadata)
            content_type = 'text/plain'
        
        return api_response(
            data={
                'export': export_data,
                'format': export_format,
                'content_type': content_type,
                'filename': f"chat_{chat_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_format}"
            },
            message=f"Chat exported in {export_format} format"
        )
        
    except Exception as e:
        return ErrorHandler.internal_error(
            e,
            f"exporting chat {chat_id}",
            "Failed to export chat"
        )


def _export_chat_json(chat, messages, include_metadata: bool) -> dict:
    """Export chat as JSON format."""
    export_data = {
        'chat_id': chat.id,
        'title': chat.title,
        'messages': []
    }
    
    if include_metadata:
        export_data['metadata'] = {
            'created_at': chat.created_at.isoformat(),
            'updated_at': chat.updated_at.isoformat(),
            'exported_at': datetime.utcnow().isoformat(),
            'message_count': len(messages)
        }
    
    for msg in messages:
        message_data = {
            'content': msg.content,
            'is_user': msg.is_user,
            'timestamp': msg.created_at.isoformat()
        }
        if include_metadata:
            message_data['model_name'] = msg.model_name
        
        export_data['messages'].append(message_data)
    
    return export_data


def _export_chat_markdown(chat, messages, include_metadata: bool) -> str:
    """Export chat as Markdown format."""
    lines = [f"# {chat.title}", ""]
    
    if include_metadata:
        lines.extend([
            "## Metadata",
            f"- **Chat ID**: {chat.id}",
            f"- **Created**: {chat.created_at.isoformat()}",
            f"- **Updated**: {chat.updated_at.isoformat()}",
            f"- **Messages**: {len(messages)}",
            f"- **Exported**: {datetime.utcnow().isoformat()}",
            "",
            "---",
            ""
        ])
    
    for msg in messages:
        role = "**User**" if msg.is_user else "**Assistant**"
        timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
        
        lines.extend([
            f"## {role} ({timestamp})",
            "",
            msg.content,
            ""
        ])
    
    return "\n".join(lines)


def _export_chat_text(chat, messages, include_metadata: bool) -> str:
    """Export chat as plain text format."""
    lines = [f"Chat: {chat.title}", "=" * (len(chat.title) + 6), ""]
    
    if include_metadata:
        lines.extend([
            f"Chat ID: {chat.id}",
            f"Created: {chat.created_at.isoformat()}",
            f"Updated: {chat.updated_at.isoformat()}",
            f"Messages: {len(messages)}",
            f"Exported: {datetime.utcnow().isoformat()}",
            "",
            "-" * 50,
            ""
        ])
    
    for msg in messages:
        role = "USER" if msg.is_user else "ASSISTANT"
        timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
        
        lines.extend([
            f"[{timestamp}] {role}:",
            msg.content,
            ""
        ])
    
    return "\n".join(lines)