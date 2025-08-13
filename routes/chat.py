from flask import Blueprint, jsonify, request, current_app as app
from flask_login import login_required, current_user
from database_operations import ChatOperations, MessageOperations, SettingsOperations
from ollama_client import OllamaClient, OllamaConnectionError

chat_bp = Blueprint('chat', __name__)

def get_user_ollama_client(user_id):
    """Get OLLAMA client configured for specific user"""
    user_settings = SettingsOperations.get_user_settings(user_id)
    return OllamaClient(user_settings.ollama_host)

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
        data = request.get_json()
        title = data.get('title') if data else None
        
        try:
            chat = ChatOperations.create_chat(current_user.id, title)
            return jsonify({
                'id': chat.id,
                'title': chat.get_title(),
                'created_at': chat.created_at.isoformat(),
                'message_count': 0
            }), 201
        except Exception as e:
            app.logger.error(f"Error creating chat for user {current_user.id}: {str(e)}")
            return jsonify({'error': f'Chyba pri vytváraní chatu: {str(e)}'}), 500

@chat_bp.route('/api/chats/<int:chat_id>', methods=['GET', 'DELETE', 'PUT'])
@login_required
def api_chat_detail(chat_id):
    """API endpoint for specific chat operations"""
    if request.method == 'GET':
        # Get chat with messages
        chat = ChatOperations.get_chat_by_id(chat_id, current_user.id)
        if not chat:
            return jsonify({'error': 'Chat nenájdený'}), 404
        
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
            return jsonify({'error': 'Chat nenájdený alebo nemáte oprávnenie'}), 404
    
    elif request.method == 'PUT':
        # Update chat (e.g., title)
        data = request.get_json()
        if not data or 'title' not in data:
            return jsonify({'error': 'Chýba title v požiadavke'}), 400
        
        chat = ChatOperations.update_chat_title(chat_id, current_user.id, data['title'])
        if chat:
            return jsonify({
                'id': chat.id,
                'title': chat.title,
                'created_at': chat.created_at.isoformat()
            })
        else:
            return jsonify({'error': 'Chat nenájdený alebo nemáte oprávnenie'}), 404

@chat_bp.route('/api/messages', methods=['POST'])
@login_required
def api_send_message():
    """API endpoint for sending messages to AI"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Chýbajú dáta v požiadavke'}), 400
    
    chat_id = data.get('chat_id')
    message_content = data.get('message', '').strip()
    model_name = data.get('model', 'gpt-oss:20b')
    
    if not chat_id or not message_content:
        return jsonify({'error': 'Chýba chat_id alebo message'}), 400
    
    # Verify user owns the chat
    chat = ChatOperations.get_chat_by_id(chat_id, current_user.id)
    if not chat:
        return jsonify({'error': 'Chat nenájdený alebo nemáte oprávnenie'}), 404
    
    try:
        # Save user message
        user_message = MessageOperations.add_message(
            chat_id=chat_id,
            content=message_content,
            is_user=True
        )
        
        # Get OLLAMA client for user
        client = get_user_ollama_client(current_user.id)
        
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
        
        # Add current user message
        conversation.append({
            "role": "user", 
            "content": message_content
        })
        
        # Send to OLLAMA
        app.logger.info(f"Sending chat request to model {model_name} for user {current_user.id}")
        response = client.chat(model_name, conversation)
        ai_content = response.get('message', {}).get('content', 'Chyba: Prázdna odpoveď')
        app.logger.info(f"Received response from model {model_name}, length: {len(ai_content)} chars")
        
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
        return jsonify({
            'error': f'Chyba komunikácie s AI: {str(e)}',
            'user_message': {
                'id': user_message.id,
                'content': user_message.content,
                'is_user': True,
                'created_at': user_message.created_at.isoformat()
            }
        }), 500
    except Exception as e:
        return jsonify({
            'error': f'Neočakávaná chyba: {str(e)}',
            'user_message': {
                'id': user_message.id if 'user_message' in locals() else None,
                'content': message_content,
                'is_user': True,
                'created_at': user_message.created_at.isoformat() if 'user_message' in locals() else None
            }
        }), 500