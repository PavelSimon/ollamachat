"""
API v1 - Models endpoints.

Enhanced model management endpoints with caching, detailed metadata,
and improved error handling.
"""

from flask import jsonify
from flask_login import login_required, current_user

from database_operations import SettingsOperations
from ollama_client import OllamaConnectionError
from ollama_pool import get_pooled_client
from response_cache import cached_models, invalidate_models_cache
from error_handlers import ErrorHandler
from enhanced_logging import get_logger, log_api_call, log_external_service_call

from . import api_v1_bp
from .base import track_request, api_response, api_error


@cached_models(ttl=300)  # Cache for 5 minutes
def _get_models_from_host(host: str):
    """
    Internal function to get models from specific host (cached).
    
    This function is cached to avoid repeated API calls to the same OLLAMA server.
    """
    client = get_pooled_client(host)
    models = client.get_models()
    
    # Enhance model data with additional metadata
    enhanced_models = []
    for model in models:
        enhanced_model = {
            **model,
            'size_human': _format_model_size(model.get('size', 0)),
            'category': _categorize_model(model.get('name', '')),
            'capabilities': _get_model_capabilities(model.get('name', ''))
        }
        enhanced_models.append(enhanced_model)
    
    return enhanced_models


def _format_model_size(size_bytes: int) -> str:
    """Format model size in human-readable format."""
    if size_bytes == 0:
        return 'Unknown'
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.1f} PB"


def _categorize_model(model_name: str) -> str:
    """Categorize model based on name patterns."""
    name_lower = model_name.lower()
    
    if 'llama' in name_lower:
        return 'LLaMA Family'
    elif 'mistral' in name_lower:
        return 'Mistral Family'
    elif 'codellama' in name_lower:
        return 'Code Specialized'
    elif 'vicuna' in name_lower:
        return 'Vicuna Family'
    elif 'alpaca' in name_lower:
        return 'Alpaca Family'
    else:
        return 'Other'


def _get_model_capabilities(model_name: str) -> list:
    """Determine model capabilities based on name patterns."""
    name_lower = model_name.lower()
    capabilities = ['Text Generation']
    
    if 'code' in name_lower:
        capabilities.append('Code Generation')
    if 'instruct' in name_lower:
        capabilities.append('Instruction Following')
    if 'chat' in name_lower:
        capabilities.append('Conversational')
    if 'uncensored' in name_lower:
        capabilities.append('Uncensored')
    
    return capabilities


@api_v1_bp.route('/models')
@login_required
@track_request()
def get_models():
    """
    Get available OLLAMA models with enhanced metadata.
    
    Returns:
        JSON response with models list including:
        - Basic model info (name, size, modified_at, digest)
        - Human-readable size formatting
        - Model categorization
        - Capability detection
        - Cache information
    """
    logger = get_logger(__name__)
    try:
        user_settings = SettingsOperations.get_user_settings(current_user.id)
        
        log_api_call(
            endpoint='/api/v1/models',
            method='GET',
            user_id=current_user.id,
            host=user_settings.ollama_host
        )
        
        # Use cached function to get enhanced models
        import time
        start_time = time.time()
        models = _get_models_from_host(user_settings.ollama_host)
        response_time = (time.time() - start_time) * 1000
        
        log_external_service_call(
            service='ollama',
            operation='get_models',
            response_time=response_time,
            host=user_settings.ollama_host,
            model_count=len(models)
        )
        
        response_data = {
            'models': models,
            'total_count': len(models),
            'host': user_settings.ollama_host,
            'cache_info': {
                'cached': True,
                'ttl_seconds': 300
            }
        }
        
        logger.info(
            f"Successfully retrieved {len(models)} models for user {current_user.id}",
            extra={
                'event': 'models_retrieved',
                'user_id': current_user.id,
                'host': user_settings.ollama_host,
                'model_count': len(models),
                'response_time_ms': response_time
            }
        )
        
        return api_response(
            data=response_data,
            message=f"Successfully retrieved {len(models)} models"
        )
        
    except OllamaConnectionError as e:
        host = user_settings.ollama_host if 'user_settings' in locals() else 'unknown'
        logger.error(
            f"OLLAMA connection failed for user {current_user.id}",
            extra={
                'event': 'ollama_connection_error',
                'user_id': current_user.id,
                'host': host,
                'error_type': 'OllamaConnectionError',
                'error_message': str(e)
            },
            exc_info=True
        )
        
        return api_error(
            'external_service_error',
            'Could not connect to OLLAMA server',
            {
                'host': host,
                'original_error': str(e)
            },
            503
        )
    except Exception as e:
        logger.error(
            f"Unexpected error loading models for user {current_user.id}",
            extra={
                'event': 'models_load_error',
                'user_id': current_user.id,
                'error_type': type(e).__name__,
                'error_message': str(e)
            },
            exc_info=True
        )
        
        return ErrorHandler.internal_error(
            e,
            "loading OLLAMA models in v1 API",
            "Failed to load models"
        )


@api_v1_bp.route('/models/refresh', methods=['POST'])
@login_required
@track_request()
def refresh_models():
    """
    Refresh models cache for current user's OLLAMA host.
    
    Forces a cache refresh by invalidating cached data and fetching fresh models.
    """
    try:
        user_settings = SettingsOperations.get_user_settings(current_user.id)
        host = user_settings.ollama_host
        
        # Invalidate cache for this host
        invalidate_models_cache(host)
        
        # Fetch fresh models (this will populate cache again)
        models = _get_models_from_host(host)
        
        response_data = {
            'models': models,
            'total_count': len(models),
            'host': host,
            'cache_info': {
                'refreshed': True,
                'timestamp': 'just_now'
            }
        }
        
        return api_response(
            data=response_data,
            message=f"Successfully refreshed {len(models)} models"
        )
        
    except Exception as e:
        return ErrorHandler.internal_error(
            e,
            "refreshing models cache in v1 API",
            "Failed to refresh models"
        )


@api_v1_bp.route('/models/<model_name>')
@login_required  
@track_request()
def get_model_details(model_name: str):
    """
    Get detailed information about a specific model.
    
    Args:
        model_name: Name of the model to get details for
        
    Returns:
        JSON response with detailed model information
    """
    try:
        user_settings = SettingsOperations.get_user_settings(current_user.id)
        models = _get_models_from_host(user_settings.ollama_host)
        
        # Find the requested model
        model = None
        for m in models:
            if m['name'] == model_name:
                model = m
                break
        
        if not model:
            return api_error(
                'not_found',
                f'Model "{model_name}" not found',
                {
                    'available_models': [m['name'] for m in models[:5]],  # Show first 5
                    'total_available': len(models)
                },
                404
            )
        
        return api_response(
            data={'model': model},
            message=f"Model details for {model_name}"
        )
        
    except Exception as e:
        return ErrorHandler.internal_error(
            e,
            f"getting model details for {model_name}",
            "Failed to get model details"
        )