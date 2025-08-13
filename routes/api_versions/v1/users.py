"""
API v1 - User endpoints.

User profile, settings, and preferences management.
"""

from flask import jsonify, request
from flask_login import login_required, current_user
from marshmallow import ValidationError

from database_operations import SettingsOperations, UserOperations
from validation_schemas import SettingsUpdateSchema, validate_request_data
from error_handlers import ErrorHandler

from . import api_v1_bp
from .base import track_request, api_response, api_error, validate_json


@api_v1_bp.route('/user/profile')
@login_required
@track_request()
def get_user_profile():
    """
    Get current user's profile information.
    
    Returns user details, preferences, and usage statistics.
    """
    try:
        user = current_user
        user_settings = SettingsOperations.get_user_settings(user.id)
        
        # Get user statistics (could be enhanced with more metrics)
        from database_operations import ChatOperations, MessageOperations
        user_chats = ChatOperations.get_user_chats(user.id)
        
        total_messages = 0
        for chat in user_chats:
            messages = MessageOperations.get_chat_messages(chat.id, user.id)
            total_messages += len(messages)
        
        profile_data = {
            'user': {
                'id': user.id,
                'email': user.email,
                'created_at': user.created_at.isoformat() if hasattr(user, 'created_at') else None
            },
            'settings': {
                'ollama_host': user_settings.ollama_host,
                'updated_at': user_settings.updated_at.isoformat() if hasattr(user_settings, 'updated_at') else None
            },
            'statistics': {
                'total_chats': len(user_chats),
                'total_messages': total_messages,
                'avg_messages_per_chat': round(total_messages / max(len(user_chats), 1), 1)
            }
        }
        
        return api_response(
            data=profile_data,
            message="User profile retrieved successfully"
        )
        
    except Exception as e:
        return ErrorHandler.internal_error(
            e,
            "getting user profile",
            "Failed to retrieve user profile"
        )


@api_v1_bp.route('/user/settings')
@login_required
@track_request()
def get_user_settings():
    """
    Get current user's settings.
    """
    try:
        user_settings = SettingsOperations.get_user_settings(current_user.id)
        
        settings_data = {
            'ollama_host': user_settings.ollama_host,
            'updated_at': user_settings.updated_at.isoformat() if hasattr(user_settings, 'updated_at') else None
        }
        
        return api_response(
            data={'settings': settings_data},
            message="User settings retrieved successfully"
        )
        
    except Exception as e:
        return ErrorHandler.internal_error(
            e,
            "getting user settings",
            "Failed to retrieve user settings"
        )


@api_v1_bp.route('/user/settings', methods=['PUT'])
@login_required
@track_request()
@validate_json()
def update_user_settings():
    """
    Update current user's settings.
    
    Request Body:
        - ollama_host: OLLAMA server URL
    """
    try:
        data = request.get_json()
        
        # Validate using existing schema
        schema = SettingsUpdateSchema()
        validated_data = validate_request_data(schema, data)
        
        # Update settings
        success = SettingsOperations.update_ollama_host(
            current_user.id,
            validated_data['ollama_host']
        )
        
        if not success:
            return api_error(
                'update_failed',
                'Failed to update user settings',
                {},
                500
            )
        
        # Get updated settings
        updated_settings = SettingsOperations.get_user_settings(current_user.id)
        
        settings_data = {
            'ollama_host': updated_settings.ollama_host,
            'updated_at': updated_settings.updated_at.isoformat() if hasattr(updated_settings, 'updated_at') else None
        }
        
        return api_response(
            data={'settings': settings_data},
            message="User settings updated successfully"
        )
        
    except ValidationError as e:
        return ErrorHandler.validation_error(e, "Invalid settings data")
    except Exception as e:
        return ErrorHandler.internal_error(
            e,
            "updating user settings",
            "Failed to update user settings"
        )


@api_v1_bp.route('/user/preferences')
@login_required
@track_request()
def get_user_preferences():
    """
    Get user preferences (can be extended for UI preferences, themes, etc.).
    
    Placeholder for future user preference features.
    """
    try:
        # For now, return basic preferences
        # This can be extended with a proper preferences table/system
        preferences_data = {
            'theme': 'light',  # Default theme
            'language': 'sk',  # Default language
            'notifications': {
                'email': False,
                'browser': True
            },
            'ui': {
                'compact_mode': False,
                'show_timestamps': True,
                'auto_scroll': True
            }
        }
        
        return api_response(
            data={'preferences': preferences_data},
            message="User preferences retrieved successfully (default values)"
        )
        
    except Exception as e:
        return ErrorHandler.internal_error(
            e,
            "getting user preferences",
            "Failed to retrieve user preferences"
        )


@api_v1_bp.route('/user/activity')
@login_required
@track_request()
def get_user_activity():
    """
    Get user activity summary and recent activity.
    """
    try:
        from database_operations import ChatOperations, MessageOperations
        from datetime import datetime, timedelta
        
        # Get recent activity (last 30 days)
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        user_chats = ChatOperations.get_user_chats(current_user.id)
        recent_chats = [
            chat for chat in user_chats 
            if hasattr(chat, 'updated_at') and chat.updated_at > cutoff_date
        ]
        
        # Calculate activity metrics
        activity_data = {
            'recent_activity': {
                'last_30_days': {
                    'chats_created': len([
                        chat for chat in recent_chats 
                        if hasattr(chat, 'created_at') and chat.created_at > cutoff_date
                    ]),
                    'chats_updated': len(recent_chats),
                    'total_chats': len(user_chats)
                }
            },
            'most_recent_chats': []
        }
        
        # Get most recent chats
        sorted_chats = sorted(
            user_chats, 
            key=lambda x: x.updated_at if hasattr(x, 'updated_at') else x.created_at,
            reverse=True
        )[:5]
        
        for chat in sorted_chats:
            messages = MessageOperations.get_chat_messages(chat.id, current_user.id)
            chat_data = {
                'id': chat.id,
                'title': chat.title,
                'updated_at': chat.updated_at.isoformat() if hasattr(chat, 'updated_at') else None,
                'message_count': len(messages)
            }
            activity_data['most_recent_chats'].append(chat_data)
        
        return api_response(
            data=activity_data,
            message="User activity retrieved successfully"
        )
        
    except Exception as e:
        return ErrorHandler.internal_error(
            e,
            "getting user activity",
            "Failed to retrieve user activity"
        )