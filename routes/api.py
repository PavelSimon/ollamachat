from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from database_operations import SettingsOperations
from ollama_client import OllamaClient, OllamaConnectionError
from error_handlers import ErrorHandler

api_bp = Blueprint('api', __name__)

def get_user_ollama_client(user_id):
    """
    Get OLLAMA client configured for specific user.
    
    Args:
        user_id (int): The user ID to get settings for
        
    Returns:
        OllamaClient: Configured client with user's OLLAMA host settings
    """
    user_settings = SettingsOperations.get_user_settings(user_id)
    return OllamaClient(user_settings.ollama_host)

@api_bp.route('/api/test-connection')
@login_required
def test_connection():
    """
    Test connection to user's configured OLLAMA server.
    
    GET endpoint that checks if the OLLAMA server is accessible and responding.
    Uses the user's configured OLLAMA host from their settings.
    
    Returns:
        JSON response:
        - connected (bool): True if connection successful
        - host (str): The OLLAMA host URL that was tested
        - error (str, optional): Error message if connection failed
        
    Status Codes:
        200: Connection test completed (check 'connected' field for result)
        500: Internal server error
    """
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
    """
    Get list of available OLLAMA models and server version information.
    
    GET endpoint that retrieves all models available on the user's OLLAMA server
    along with server version details.
    
    Returns:
        JSON response:
        - models (list): Array of model objects with name, size, modified_at, digest
        - host (str): The OLLAMA host URL that was queried
        - version (dict): Server version information including version, architecture, etc.
        
    Status Codes:
        200: Models retrieved successfully
        500: OLLAMA server error or internal server error
        
    Note:
        On error, response includes empty models array and null version for compatibility.
    """
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

