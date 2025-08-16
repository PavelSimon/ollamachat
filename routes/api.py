from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from database_operations import SettingsOperations
from ollama_client import OllamaClient, OllamaConnectionError
from error_handlers import ErrorHandler

api_bp = Blueprint('api', __name__)

def get_user_ollama_client(user_id):
    """Get OLLAMA client configured for specific user"""
    user_settings = SettingsOperations.get_user_settings(user_id)
    return OllamaClient(user_settings.ollama_host)

@api_bp.route('/api/test-connection')
@login_required
def test_connection():
    """API endpoint to test OLLAMA connection"""
    user_settings = SettingsOperations.get_user_settings(current_user.id)
    try:
        with get_user_ollama_client(current_user.id) as client:
            connected = client.test_connection()
        
        return jsonify({
            'connected': connected,
            'host': user_settings.ollama_host
        })
    except OllamaConnectionError as e:
        return jsonify({
            'connected': False,
            'error': str(e),
            'host': user_settings.ollama_host
        })
    except Exception as e:
        return ErrorHandler.external_service_error(
            "OLLAMA server",
            e,
            "Chyba pri testovaní pripojenia k OLLAMA serveru"
        )

@api_bp.route('/api/models')
@login_required
def get_models():
    """API endpoint to get available OLLAMA models"""
    user_settings = SettingsOperations.get_user_settings(current_user.id)
    try:
        # Get direct client and fetch models using context manager
        with get_user_ollama_client(current_user.id) as client:
            models = client.get_models()
            version_info = client.get_version()
        
        return jsonify({
            'models': models,
            'host': user_settings.ollama_host,
            'version': version_info
        })
    except OllamaConnectionError as e:
        # Return structured error with models list for backward compatibility
        error_response, status_code = ErrorHandler.external_service_error(
            "OLLAMA server",
            e,
            "Nemožno načítať zoznam modelov"
        )
        # Add compatibility fields
        error_response['models'] = []
        error_response['host'] = user_settings.ollama_host
        error_response['version'] = None
        return error_response, status_code
    except Exception as e:
        error_response, status_code = ErrorHandler.internal_error(
            e,
            "loading OLLAMA models",
            "Chyba pri načítavaní modelov"
        )
        # Add compatibility fields
        error_response['models'] = []
        error_response['host'] = user_settings.ollama_host
        error_response['version'] = None
        return error_response, status_code

