"""
API v1 - System endpoints.

System monitoring, health checks, and administrative endpoints.
"""

from flask import jsonify
from flask_login import login_required, current_user
import time
import platform
from datetime import datetime

# Optional import for system monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False

from database_operations import SettingsOperations
from ollama_client import OllamaConnectionError
from ollama_pool import get_pooled_client, get_pool_stats
from response_cache import get_cache_stats
from error_handlers import ErrorHandler

from . import api_v1_bp
from .base import track_request, api_response, api_error


@api_v1_bp.route('/health')
@track_request()
def health_check():
    """
    Comprehensive health check endpoint.
    
    Returns system health status including:
    - API health
    - Database connectivity
    - Cache status
    - Connection pool status
    - System resources (optional)
    """
    try:
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': 'v1',
            'checks': {}
        }
        
        # API Health
        health_data['checks']['api'] = {
            'status': 'healthy',
            'response_time_ms': 0  # Will be calculated
        }
        
        # Database Health
        try:
            from models import db
            from sqlalchemy import text
            # Simple query to test DB connectivity
            with db.engine.connect() as connection:
                connection.execute(text('SELECT 1'))
            health_data['checks']['database'] = {
                'status': 'healthy',
                'connection': 'ok'
            }
        except Exception as e:
            health_data['checks']['database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_data['status'] = 'degraded'
        
        # Cache Health
        try:
            cache_stats = get_cache_stats()
            health_data['checks']['cache'] = {
                'status': 'healthy',
                'model_cache_size': cache_stats['model_cache']['cache_size'],
                'general_cache_size': cache_stats['general_cache']['cache_size']
            }
        except Exception as e:
            health_data['checks']['cache'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_data['status'] = 'degraded'
        
        # Connection Pool Health
        try:
            pool_stats = get_pool_stats()
            health_data['checks']['connection_pool'] = {
                'status': 'healthy',
                'total_connections': pool_stats['total_active_connections'],
                'hit_rate': pool_stats['global_stats']['hits'] / max(1, 
                    pool_stats['global_stats']['hits'] + pool_stats['global_stats']['misses'])
            }
        except Exception as e:
            health_data['checks']['connection_pool'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_data['status'] = 'degraded'
        
        # Determine overall status
        unhealthy_checks = [
            check for check in health_data['checks'].values() 
            if check['status'] == 'unhealthy'
        ]
        
        if unhealthy_checks:
            health_data['status'] = 'unhealthy'
            status_code = 503
        elif health_data['status'] == 'degraded':
            status_code = 200  # Degraded but still functional
        else:
            status_code = 200
        
        return api_response(
            data=health_data,
            message=f"System status: {health_data['status']}",
            status_code=status_code
        )
        
    except Exception as e:
        return ErrorHandler.internal_error(
            e,
            "performing health check",
            "Health check failed"
        )


@api_v1_bp.route('/status')
@login_required
@track_request()
def system_status():
    """
    Detailed system status endpoint for authenticated users.
    
    Includes more detailed system information and metrics.
    """
    try:
        status_data = {
            'system': {
                'platform': platform.system(),
                'platform_version': platform.version(),
                'python_version': platform.python_version(),
                'architecture': platform.machine(),
                'processor': platform.processor() or 'Unknown'
            },
            'resources': {},
            'application': {
                'version': 'v1',
                'uptime_seconds': time.time() - getattr(system_status, 'start_time', time.time())
            },
            'services': {}
        }
        
        # System Resources (if available)
        if PSUTIL_AVAILABLE and psutil:
            try:
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                status_data['resources'] = {
                    'memory': {
                        'total_mb': round(memory.total / 1024 / 1024),
                        'available_mb': round(memory.available / 1024 / 1024),
                        'used_percent': memory.percent
                    },
                    'disk': {
                        'total_gb': round(disk.total / 1024 / 1024 / 1024),
                        'free_gb': round(disk.free / 1024 / 1024 / 1024),
                        'used_percent': round((disk.used / disk.total) * 100, 1)
                    },
                    'cpu_percent': psutil.cpu_percent(interval=1)
                }
            except Exception:
                status_data['resources'] = {'status': 'unavailable', 'reason': 'psutil error'}
        else:
            status_data['resources'] = {'status': 'unavailable', 'reason': 'psutil not installed'}
        
        # Service Status
        try:
            # Connection Pool Stats
            pool_stats = get_pool_stats()
            status_data['services']['connection_pool'] = {
                'total_connections': pool_stats['total_active_connections'],
                'stats': pool_stats['global_stats']
            }
            
            # Cache Stats
            cache_stats = get_cache_stats()
            status_data['services']['cache'] = cache_stats
            
        except Exception as e:
            status_data['services']['error'] = str(e)
        
        return api_response(
            data=status_data,
            message="System status retrieved successfully"
        )
        
    except Exception as e:
        return ErrorHandler.internal_error(
            e,
            "getting system status",
            "Failed to get system status"
        )


@api_v1_bp.route('/connection/test')
@login_required
@track_request()
def test_ollama_connection():
    """
    Test OLLAMA server connection for current user.
    
    Enhanced version of connection test with detailed diagnostics.
    """
    try:
        user_settings = SettingsOperations.get_user_settings(current_user.id)
        client = get_pooled_client(user_settings.ollama_host)
        
        start_time = time.time()
        connected = client.test_connection()
        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        connection_data = {
            'connected': connected,
            'host': user_settings.ollama_host,
            'response_time_ms': round(response_time, 2),
            'status': 'success' if connected else 'failed',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if connected:
            # If connected, try to get additional server info
            try:
                models = client.get_models()
                connection_data['server_info'] = {
                    'model_count': len(models),
                    'available': True
                }
            except Exception:
                connection_data['server_info'] = {
                    'available': False,
                    'note': 'Connected but model listing failed'
                }
        
        return api_response(
            data=connection_data,
            message=f"Connection test {'successful' if connected else 'failed'}"
        )
        
    except OllamaConnectionError as e:
        user_settings = SettingsOperations.get_user_settings(current_user.id)
        return api_error(
            'connection_error',
            'Failed to connect to OLLAMA server',
            {
                'host': user_settings.ollama_host,
                'error': str(e)
            },
            503
        )
    except Exception as e:
        return ErrorHandler.internal_error(
            e,
            "testing OLLAMA connection",
            "Connection test failed"
        )


# Store start time for uptime calculation
if not hasattr(system_status, 'start_time'):
    system_status.start_time = time.time()