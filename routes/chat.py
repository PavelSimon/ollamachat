from flask import Blueprint, jsonify, request, current_app as app
from flask_login import login_required, current_user
from database_operations import ChatOperations, MessageOperations, SettingsOperations
from ollama_client import OllamaClient, OllamaConnectionError
from error_handlers import ErrorHandler
from rate_limiting import api_rate_limit, RateLimits
import html
import re

chat_bp = Blueprint('chat', __name__)

# Import limiter after app initialization
def get_limiter():
    from app import get_limiter
    return get_limiter()

def sanitize_message_content(content):
    """Sanitize user message content for security"""
    if not content:
        return content
    
    # Strip whitespace
    content = content.strip()
    
    # Limit message length
    if len(content) > 10000:
        content = content[:10000]
    
    # Remove potentially dangerous characters but keep basic formatting
    # Allow letters, numbers, spaces, basic punctuation, and common symbols
    content = re.sub(r'[^\w\s\.\,\?\!\-\(\)\[\]\{\}\:\;\"\'\`\~\@\#\$\%\^\&\*\+\=\_\|\\\/<>]', '', content)
    
    # Escape HTML to prevent XSS
    content = html.escape(content, quote=True)
    
    return content

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
            title = data.get('title')
            
            # Simple validation and sanitization
            if title:
                title = html.escape(title.strip(), quote=True)
                if len(title) > 200:
                    return jsonify({'error': 'Titol je príliš dlhý (max 200 znakov)'}), 400
            
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
                return jsonify({'error': 'Chýbajú dáta v požiadavke'}), 400
            
            title = data.get('title', '').strip()
            if not title:
                return jsonify({'error': 'Chýba titol'}), 400
            
            # Sanitize title
            title = html.escape(title, quote=True)
            if len(title) > 200:
                return jsonify({'error': 'Titol je príliš dlhý (max 200 znakov)'}), 400
            
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
            return jsonify({'error': 'Chýbajú dáta v požiadavke'}), 400
        
        chat_ids = data.get('chat_ids', [])
        if not chat_ids or not isinstance(chat_ids, list):
            return jsonify({'error': 'Chýba zoznam chat_ids'}), 400
        
        # Validate that all chat_ids are integers
        try:
            chat_ids = [int(chat_id) for chat_id in chat_ids]
        except (ValueError, TypeError):
            return jsonify({'error': 'Neplatné chat_ids - musia byť čísla'}), 400
        
        if len(chat_ids) > 100:  # Reasonable limit
            return jsonify({'error': 'Príliš veľa chatov na vymazanie naraz (max 100)'}), 400
        
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
            return jsonify({'error': 'Chýbajú dáta v požiadavke'}), 400
        
        # Simple validation and sanitization
        chat_id = data.get('chat_id')
        raw_message_content = data.get('message', '')
        model_name = data.get('model', 'gpt-oss:20b')
        use_internet_search = data.get('use_internet_search', False)
        
        # Sanitize the message content
        message_content = sanitize_message_content(raw_message_content)
        
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