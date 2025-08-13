from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from database_operations import SettingsOperations
from ollama_client import OllamaClient, OllamaConnectionError

api_bp = Blueprint('api', __name__)

def get_user_ollama_client(user_id):
    """Get OLLAMA client configured for specific user"""
    user_settings = SettingsOperations.get_user_settings(user_id)
    return OllamaClient(user_settings.ollama_host)

@api_bp.route('/api/test-connection')
@login_required
def test_connection():
    """API endpoint to test OLLAMA connection"""
    try:
        client = get_user_ollama_client(current_user.id)
        user_settings = SettingsOperations.get_user_settings(current_user.id)
        connected = client.test_connection()
        
        return jsonify({
            'connected': connected,
            'host': user_settings.ollama_host
        })
    except Exception as e:
        user_settings = SettingsOperations.get_user_settings(current_user.id)
        return jsonify({
            'connected': False,
            'error': str(e),
            'host': user_settings.ollama_host
        })

@api_bp.route('/api/models')
@login_required
def get_models():
    """API endpoint to get available OLLAMA models"""
    user_settings = SettingsOperations.get_user_settings(current_user.id)
    try:
        client = get_user_ollama_client(current_user.id)
        models = client.get_models()
        
        return jsonify({
            'models': models,
            'host': user_settings.ollama_host
        })
    except OllamaConnectionError as e:
        return jsonify({
            'error': str(e),
            'models': [],
            'host': user_settings.ollama_host
        }), 400
    except Exception as e:
        return jsonify({
            'error': f'Neočakávaná chyba: {str(e)}',
            'models': [],
            'host': user_settings.ollama_host
        }), 500