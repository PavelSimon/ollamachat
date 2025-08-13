from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from database_operations import SettingsOperations
from ollama_client import OllamaConnectionError
from ollama_pool import get_pooled_client, get_pool_stats
from error_handlers import ErrorHandler
from response_cache import cached_models, get_cache_stats, invalidate_models_cache

api_bp = Blueprint('api', __name__)

def get_user_ollama_client(user_id):
    """Get pooled OLLAMA client configured for specific user"""
    user_settings = SettingsOperations.get_user_settings(user_id)
    return get_pooled_client(user_settings.ollama_host)


@cached_models(ttl=300)  # Cache for 5 minutes
def _get_models_from_host(host: str):
    """
    Internal function to get models from specific host (cached).
    
    This function is cached to avoid repeated API calls to the same OLLAMA server.
    """
    client = get_pooled_client(host)
    return client.get_models()

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
    except OllamaConnectionError as e:
        user_settings = SettingsOperations.get_user_settings(current_user.id)
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
    """API endpoint to get available OLLAMA models (cached)"""
    user_settings = SettingsOperations.get_user_settings(current_user.id)
    try:
        # Use cached function to get models
        models = _get_models_from_host(user_settings.ollama_host)
        
        # Get version information
        client = get_user_ollama_client(current_user.id)
        version_info = client.get_version()
        
        return jsonify({
            'models': models,
            'host': user_settings.ollama_host,
            'version': version_info,
            'cached': True  # Indicate that response may be cached
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


@api_bp.route('/api/pool-stats')
@login_required
def get_connection_pool_stats():
    """API endpoint to get OLLAMA connection pool statistics"""
    try:
        stats = get_pool_stats()
        return jsonify(stats)
    except Exception as e:
        return ErrorHandler.internal_error(
            e,
            "getting pool statistics",
            "Chyba pri načítavaní štatistík pripojení"
        )


@api_bp.route('/api/cache-stats')
@login_required
def get_cache_statistics():
    """API endpoint to get response cache statistics"""
    try:
        stats = get_cache_stats()
        return jsonify(stats)
    except Exception as e:
        return ErrorHandler.internal_error(
            e,
            "getting cache statistics",
            "Chyba pri načítavaní štatistík cache"
        )


@api_bp.route('/api/cache/models/clear', methods=['POST'])
@login_required
def clear_models_cache():
    """API endpoint to clear the models cache"""
    try:
        # Get user's host to optionally clear only that host's cache
        user_settings = SettingsOperations.get_user_settings(current_user.id)
        host = user_settings.ollama_host
        
        # Clear cache for this user's host only
        invalidate_models_cache(host)
        
        return jsonify({
            'message': 'Models cache cleared successfully',
            'host': host
        })
    except Exception as e:
        return ErrorHandler.internal_error(
            e,
            "clearing models cache",
            "Chyba pri mazaní cache modelov"
        )