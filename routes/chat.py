from flask import Blueprint, jsonify, request, current_app as app
from flask_login import login_required, current_user
from database_operations import ChatOperations, MessageOperations, SettingsOperations
from ollama_client import OllamaClient, OllamaConnectionError
# from search_service import search_service  # Temporarily disabled
from error_handlers import ErrorHandler
from rate_limiting import api_rate_limit, RateLimits

chat_bp = Blueprint('chat', __name__)

# Import limiter after app initialization
def get_limiter():
    from app import get_limiter
    return get_limiter()

# Simplified - removed complex pooling for now

@chat_bp.route('/api/chats', methods=['GET', 'POST'])
@login_required
def api_chats():
    """API endpoint for chat management"""
    if request.method == 'GET':
        # Get all user chats
        chats = ChatOperations.get_user_chats(current_user.id)
        chat_list = []
        
        for chat in chats:
            chat_data = {
                'id': chat.id,
                'title': chat.get_title(),
                'created_at': chat.created_at.isoformat(),
                'message_count': len(chat.messages)
            }
            chat_list.append(chat_data)
        
        return jsonify({'chats': chat_list})
    
    elif request.method == 'POST':
        # Create new chat
        try:
            data = request.get_json() or {}
            validated_data = validate_request_data(ChatCreateSchema, data)
            
            chat = ChatOperations.create_chat(current_user.id, validated_data['title'])
            return jsonify({
                'id': chat.id,
                'title': chat.get_title(),
                'created_at': chat.created_at.isoformat(),
                'message_count': 0
            }), 201
        except ValidationError as e:
            return jsonify(create_validation_error_response(e)[0]), 400
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
                return jsonify({'error': 'Chýbajú dáta v požiadavke'}), 400
            
            validated_data = validate_request_data(ChatUpdateSchema, data)
            
            chat = ChatOperations.update_chat_title(chat_id, current_user.id, validated_data['title'])
            if chat:
                return jsonify({
                    'id': chat.id,
                    'title': chat.title,
                    'created_at': chat.created_at.isoformat()
                })
            else:
                return ErrorHandler.not_found("Chat", "Chat nenájdený alebo nemáte oprávnenie")
        except ValidationError as e:
            return jsonify(create_validation_error_response(e)[0]), 400

@chat_bp.route('/api/messages', methods=['POST'])
@login_required
def api_send_message():
    """API endpoint for sending messages to AI"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Chýbajú dáta v požiadavke'}), 400
        
        # Simple validation (bypass complex schema temporarily)
        chat_id = data.get('chat_id')
        message_content = data.get('message', '').strip()
        model_name = data.get('model', 'gpt-oss:20b')
        use_internet_search = data.get('use_internet_search', False)
        
        if not chat_id or not message_content:
            return jsonify({'error': 'Chýba chat_id alebo message'}), 400
        
        # Verify user owns the chat
        chat = ChatOperations.get_chat_by_id(chat_id, current_user.id)
        if not chat:
            return jsonify({'error': 'Chat nenájdený alebo nemáte oprávnenie'}), 404
        # Save user message
        user_message = MessageOperations.add_message(
            chat_id=chat_id,
            content=message_content,
            is_user=True
        )
        
        # Get OLLAMA client for user (direct approach)
        user_settings = SettingsOperations.get_user_settings(current_user.id)
        client = OllamaClient(user_settings.ollama_host)
        
        # Prepare conversation history for context
        recent_messages = MessageOperations.get_latest_messages(chat_id, limit=10)
        conversation = []
        
        # Add recent messages to conversation (reverse order for chronological)
        for msg in reversed(recent_messages):
            role = "user" if msg.is_user else "assistant"
            conversation.append({
                "role": role,
                "content": msg.content
            })
        
        # Handle internet search if requested (temporarily disabled)
        final_message = message_content
        
        if use_internet_search:
            # Search temporarily disabled for debugging
            app.logger.info("Internet search requested but temporarily disabled")
            final_message = f"[Internet search temporarily disabled] {message_content}"
        
        # Add current user message
        conversation.append({
            "role": "user", 
            "content": final_message
        })
        
        # Send to OLLAMA
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
        if not chat.title and len(chat.messages) <= 2:  # User + AI message
            # Generate title from first user message
            title = message_content[:50] + "..." if len(message_content) > 50 else message_content
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
        app.logger.error(f"OLLAMA connection error: {e}")
        return jsonify({
            'error': f'Chyba komunikácie s AI: {str(e)}'
        }), 500
    except Exception as e:
        app.logger.error(f"Unexpected error in chat: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'Neočakávaná chyba: {str(e)}'
        }), 500