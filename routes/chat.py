from flask import Blueprint, jsonify, request, current_app as app
from flask_login import login_required, current_user
from database_operations import ChatOperations, MessageOperations, SettingsOperations
from ollama_client import OllamaClient, OllamaConnectionError
from error_handlers import ErrorHandler, StandardError, ErrorType
from rate_limiting import api_rate_limit, RateLimits
import html
import re

chat_bp = Blueprint('chat', __name__)

def get_limiter():
    from app import get_limiter
    return get_limiter()

def sanitize_message_content(content):
    """
    Sanitize user message content for security and length limits.
    
    Args:
        content (str): Raw user input message content
        
    Returns:
        str: Sanitized content with:
            - Whitespace trimmed
            - Length limited to MAX_MESSAGE_LENGTH
            - Dangerous characters filtered out
            - HTML escaped for XSS prevention
            
    Note:
        Allows basic formatting characters and common symbols while
        removing potentially dangerous input.
    """
    if not content:
        return content
    
    # Strip whitespace
    content = content.strip()
    
    # Limit message length
    if len(content) > app.config['MAX_MESSAGE_LENGTH']:
        content = content[:app.config['MAX_MESSAGE_LENGTH']]
    
    # Remove potentially dangerous characters but keep basic formatting
    # Allow letters, numbers, spaces, basic punctuation, and common symbols
    content = re.sub(r'[^\w\s\.\,\?\!\-\(\)\[\]\{\}\:\;\"\'\`\~\@\#\$\%\^\&\*\+\=\_\|\\\/<>]', '', content)
    
    # Escape HTML to prevent XSS
    content = html.escape(content, quote=True)
    
    return content


@chat_bp.route('/api/chats', methods=['GET', 'POST'])
@login_required
def api_chats():
    """
    Chat management API endpoint.
    
    GET: Retrieve all user's chats with message counts
    POST: Create a new chat with optional title
    
    GET Returns:
        JSON response:
        - chats (list): Array of chat objects with:
          - id (int): Chat ID
          - title (str): Chat title or auto-generated from first message
          - created_at (str): ISO timestamp
          - message_count (int): Number of messages in chat
          
    POST Request Body:
        - title (str, optional): Chat title (max MAX_TITLE_LENGTH chars)
        
    POST Returns:
        JSON response:
        - id (int): New chat ID
        - title (str): Chat title
        - created_at (str): ISO timestamp
        - message_count (int): Always 0 for new chats
        
    Status Codes:
        200: GET successful
        201: POST successful (chat created)
        400: Validation error (title too long, invalid data)
        500: Internal server error
    """
    if request.method == 'GET':
        # Get all user chats with message counts in single query (prevents N+1)
        chats_with_counts = ChatOperations.get_user_chats_with_message_counts(current_user.id)
        chat_list = []
        
        for chat, message_count in chats_with_counts:
            chat_data = {
                'id': chat.id,
                'title': chat.get_title(),
                'created_at': chat.created_at.isoformat(),
                'message_count': message_count or 0
            }
            chat_list.append(chat_data)
        
        return jsonify({'chats': chat_list})
    
    elif request.method == 'POST':
        # Create new chat
        try:
            data = request.get_json() or {}
            title = data.get('title')
            
            # Simple validation and sanitization
            if title:
                title = html.escape(title.strip(), quote=True)
                if len(title) > app.config['MAX_TITLE_LENGTH']:
                    error = StandardError(
                    error_type=ErrorType.VALIDATION_ERROR,
                    message="Title too long",
                    user_message=f'Titol je príliš dlhý (max {app.config["MAX_TITLE_LENGTH"]} znakov)',
                    status_code=400
                )
                return jsonify(error.to_dict()), error.status_code
            
            chat = ChatOperations.create_chat(current_user.id, title)
            return jsonify({
                'id': chat.id,
                'title': chat.get_title(),
                'created_at': chat.created_at.isoformat(),
                'message_count': 0
            }), 201
        except Exception as e:
            return ErrorHandler.internal_error(
                e,
                f"creating chat for user {current_user.id}",
                "Chyba pri vytváraní chatu"
            )

@chat_bp.route('/api/chats/<int:chat_id>', methods=['GET', 'DELETE', 'PUT'])
@login_required
def api_chat_detail(chat_id):
    """API endpoint for specific chat operations"""
    if request.method == 'GET':
        # Get chat with messages
        chat = ChatOperations.get_chat_by_id(chat_id, current_user.id)
        if not chat:
            return ErrorHandler.not_found("Chat", "Chat nenájdený")
        
        messages = MessageOperations.get_chat_messages(chat_id, current_user.id)
        message_list = []
        
        for message in messages:
            message_data = {
                'id': message.id,
                'content': message.content,
                'is_user': message.is_user,
                'model_name': message.model_name,
                'created_at': message.created_at.isoformat()
            }
            message_list.append(message_data)
        
        return jsonify({
            'id': chat.id,
            'title': chat.get_title(),
            'created_at': chat.created_at.isoformat(),
            'messages': message_list
        })
    
    elif request.method == 'DELETE':
        # Delete chat
        success = ChatOperations.delete_chat(chat_id, current_user.id)
        if success:
            return jsonify({'message': 'Chat bol úspešne zmazaný'})
        else:
            return ErrorHandler.not_found("Chat", "Chat nenájdený alebo nemáte oprávnenie")
    
    elif request.method == 'PUT':
        # Update chat (e.g., title)
        try:
            data = request.get_json()
            if not data:
                error = StandardError(
                    error_type=ErrorType.VALIDATION_ERROR,
                    message="Missing request data",
                    user_message='Chýbajú dáta v požiadavke',
                    status_code=400
                )
                return jsonify(error.to_dict()), error.status_code
            
            title = data.get('title', '').strip()
            if not title:
                error = StandardError(
                    error_type=ErrorType.VALIDATION_ERROR,
                    message="Missing title",
                    user_message='Chýba titol',
                    status_code=400
                )
                return jsonify(error.to_dict()), error.status_code
            
            # Sanitize title
            title = html.escape(title, quote=True)
            if len(title) > app.config['MAX_TITLE_LENGTH']:
                error = StandardError(
                    error_type=ErrorType.VALIDATION_ERROR,
                    message="Title too long",
                    user_message=f'Titol je príliš dlhý (max {app.config["MAX_TITLE_LENGTH"]} znakov)',
                    status_code=400
                )
                return jsonify(error.to_dict()), error.status_code
            
            chat = ChatOperations.update_chat_title(chat_id, current_user.id, title)
            if chat:
                return jsonify({
                    'id': chat.id,
                    'title': chat.title,
                    'created_at': chat.created_at.isoformat()
                })
            else:
                return ErrorHandler.not_found("Chat", "Chat nenájdený alebo nemáte oprávnenie")
        except Exception as e:
            return ErrorHandler.internal_error(
                e,
                f"updating chat {chat_id} for user {current_user.id}",
                "Chyba pri aktualizácii chatu"
            )

@chat_bp.route('/api/chats/bulk-delete', methods=['POST'])
@login_required
def api_bulk_delete_chats():
    """API endpoint for bulk deleting multiple chats"""
    try:
        data = request.get_json()
        if not data:
            error = StandardError(
                error_type=ErrorType.VALIDATION_ERROR,
                message="Missing request data",
                user_message='Chýbajú dáta v požiadavke',
                status_code=400
            )
            return jsonify(error.to_dict()), error.status_code
        
        chat_ids = data.get('chat_ids', [])
        if not chat_ids or not isinstance(chat_ids, list):
            error = StandardError(
                error_type=ErrorType.VALIDATION_ERROR,
                message="Missing or invalid chat_ids",
                user_message='Chýba zoznam chat_ids',
                status_code=400
            )
            return jsonify(error.to_dict()), error.status_code
        
        # Validate that all chat_ids are integers
        try:
            chat_ids = [int(chat_id) for chat_id in chat_ids]
        except (ValueError, TypeError):
            error = StandardError(
                error_type=ErrorType.VALIDATION_ERROR,
                message="Invalid chat_ids format",
                user_message='Neplatné chat_ids - musia byť čísla',
                status_code=400
            )
            return jsonify(error.to_dict()), error.status_code
        
        if len(chat_ids) > app.config['MAX_BULK_DELETE_LIMIT']:
            error = StandardError(
                error_type=ErrorType.VALIDATION_ERROR,
                message="Too many chats to delete",
                user_message=f'Príliš veľa chatov na vymazanie naraz (max {app.config["MAX_BULK_DELETE_LIMIT"]})',
                status_code=400
            )
            return jsonify(error.to_dict()), error.status_code
        
        # Delete chats one by one and count successful deletions
        deleted_count = 0
        failed_deletions = []
        
        for chat_id in chat_ids:
            try:
                success = ChatOperations.delete_chat(chat_id, current_user.id)
                if success:
                    deleted_count += 1
                else:
                    failed_deletions.append(chat_id)
            except Exception as e:
                app.logger.error(f"Error deleting chat {chat_id} for user {current_user.id}: {e}")
                failed_deletions.append(chat_id)
        
        # Prepare response
        response_data = {
            'success': True,
            'deleted_count': deleted_count,
            'total_requested': len(chat_ids)
        }
        
        if failed_deletions:
            response_data['failed_deletions'] = failed_deletions
            response_data['message'] = f"Vymazané {deleted_count} z {len(chat_ids)} chatov. Niektoré chaty sa nepodarilo vymazať."
        else:
            response_data['message'] = f"Úspešne vymazané všetky {deleted_count} chaty."
        
        return jsonify(response_data)
        
    except Exception as e:
        return ErrorHandler.internal_error(
            e,
            f"bulk deleting chats for user {current_user.id}",
            "Chyba pri hromadnom vymazávaní chatov"
        )

@chat_bp.route('/api/messages', methods=['POST'])
@login_required
def api_send_message():
    """API endpoint for sending messages to AI"""
    try:
        data = request.get_json()
        if not data:
            error = StandardError(
                error_type=ErrorType.VALIDATION_ERROR,
                message="Missing request data",
                user_message='Chýbajú dáta v požiadavke',
                status_code=400
            )
            return jsonify(error.to_dict()), error.status_code
        
        # Simple validation and sanitization
        chat_id = data.get('chat_id')
        raw_message_content = data.get('message', '')
        model_name = data.get('model', app.config['DEFAULT_MODEL_NAME'])
        use_internet_search = data.get('use_internet_search', False)
        
        # Sanitize the message content
        message_content = sanitize_message_content(raw_message_content)
        
        if not chat_id or not message_content:
            error = StandardError(
                error_type=ErrorType.VALIDATION_ERROR,
                message="Missing chat_id or message",
                user_message='Chýba chat_id alebo message',
                status_code=400
            )
            return jsonify(error.to_dict()), error.status_code
        
        # Verify user owns the chat
        chat = ChatOperations.get_chat_by_id(chat_id, current_user.id)
        if not chat:
            return ErrorHandler.not_found("Chat", "Chat nenájdený alebo nemáte oprávnenie")
        # Save user message
        user_message = MessageOperations.add_message(
            chat_id=chat_id,
            content=message_content,
            is_user=True
        )
        
        # Get OLLAMA client for user and use as context manager for proper cleanup
        user_settings = SettingsOperations.get_user_settings(current_user.id)
        
        # Prepare conversation history for context
        recent_messages = MessageOperations.get_latest_messages(chat_id, limit=app.config['CONVERSATION_HISTORY_LIMIT'])
        conversation = []
        
        # Add recent messages to conversation (reverse order for chronological)
        for msg in reversed(recent_messages):
            role = "user" if msg.is_user else "assistant"
            conversation.append({
                "role": role,
                "content": msg.content
            })
        
        # Note: Internet search functionality has been removed for code simplicity
        # The use_internet_search parameter is ignored for now
        if use_internet_search:
            app.logger.info("Internet search functionality not available")
        
        # Add current user message
        conversation.append({
            "role": "user", 
            "content": message_content
        })
        
        # Send to OLLAMA using context manager to ensure session cleanup
        with OllamaClient(user_settings.ollama_host) as client:
            response = client.chat(model_name, conversation)
            ai_content = response.get('message', {}).get('content', 'Chyba: Prázdna odpoveď')
        
        # Save AI response
        ai_message = MessageOperations.add_message(
            chat_id=chat_id,
            content=ai_content,
            is_user=False,
            model_name=model_name
        )
        
        # Update chat title if it's the first message
        if not chat.title and len(chat.messages) <= app.config['AUTO_TITLE_MESSAGE_LIMIT']:  # User + AI message
            # Generate title from first user message
            max_length = app.config['AUTO_TITLE_MAX_LENGTH']
            title = message_content[:max_length] + "..." if len(message_content) > max_length else message_content
            ChatOperations.update_chat_title(chat_id, current_user.id, title)
        
        return jsonify({
            'user_message': {
                'id': user_message.id,
                'content': user_message.content,
                'is_user': True,
                'created_at': user_message.created_at.isoformat()
            },
            'ai_message': {
                'id': ai_message.id,
                'content': ai_message.content,
                'is_user': False,
                'model_name': ai_message.model_name,
                'created_at': ai_message.created_at.isoformat()
            },
            'stats': {
                'total_duration': response.get('total_duration', 0),
                'eval_count': response.get('eval_count', 0)
            }
        })
        
    except OllamaConnectionError as e:
        return ErrorHandler.external_service_error(
            "OLLAMA server",
            e,
            f'Chyba komunikácie s AI: {str(e)}'
        )
    except Exception as e:
        return ErrorHandler.internal_error(
            e,
            "Neočakávaná chyba pri spracovaní správy"
        )