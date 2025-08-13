"""
API v1 Documentation endpoints.

Provides basic API documentation and OpenAPI-style endpoint descriptions.
"""

from flask import jsonify

from . import api_v1_bp
from .base import track_request, api_response


@api_v1_bp.route('/docs')
@track_request()
def api_documentation():
    """
    Get API v1 documentation overview.
    
    Returns basic information about available endpoints and their usage.
    """
    documentation = {
        'api_version': 'v1',
        'description': 'OLLAMA Chat API v1 - Enhanced endpoints with proper versioning',
        'base_url': '/api/v1',
        'authentication': {
            'type': 'session',
            'description': 'Requires user login session for most endpoints',
            'public_endpoints': ['/health']
        },
        'endpoints': {
            'health': {
                'path': '/health',
                'method': 'GET',
                'description': 'System health check',
                'authentication_required': False,
                'parameters': {},
                'response': {
                    'type': 'object',
                    'properties': {
                        'status': {'type': 'string', 'enum': ['healthy', 'degraded', 'unhealthy']},
                        'checks': {'type': 'object'},
                        'timestamp': {'type': 'string', 'format': 'datetime'},
                        'version': {'type': 'string'}
                    }
                }
            },
            'system_status': {
                'path': '/status',
                'method': 'GET',
                'description': 'Detailed system status for authenticated users',
                'authentication_required': True,
                'parameters': {},
                'response': {
                    'type': 'object',
                    'properties': {
                        'system': {'type': 'object'},
                        'resources': {'type': 'object'},
                        'application': {'type': 'object'},
                        'services': {'type': 'object'}
                    }
                }
            },
            'models': {
                'path': '/models',
                'method': 'GET',
                'description': 'Get available OLLAMA models with enhanced metadata',
                'authentication_required': True,
                'parameters': {},
                'response': {
                    'type': 'object',
                    'properties': {
                        'models': {'type': 'array'},
                        'total_count': {'type': 'integer'},
                        'host': {'type': 'string'},
                        'cache_info': {'type': 'object'}
                    }
                }
            },
            'refresh_models': {
                'path': '/models/refresh',
                'method': 'POST',
                'description': 'Refresh models cache',
                'authentication_required': True,
                'parameters': {},
                'response': 'Same as /models endpoint'
            },
            'model_details': {
                'path': '/models/{model_name}',
                'method': 'GET',
                'description': 'Get detailed information about a specific model',
                'authentication_required': True,
                'parameters': {
                    'model_name': {'type': 'string', 'location': 'path', 'description': 'Name of the model'}
                },
                'response': {
                    'type': 'object',
                    'properties': {
                        'model': {'type': 'object'}
                    }
                }
            },
            'test_connection': {
                'path': '/connection/test',
                'method': 'GET',
                'description': 'Test OLLAMA server connection',
                'authentication_required': True,
                'parameters': {},
                'response': {
                    'type': 'object',
                    'properties': {
                        'connected': {'type': 'boolean'},
                        'host': {'type': 'string'},
                        'response_time_ms': {'type': 'number'},
                        'status': {'type': 'string'},
                        'timestamp': {'type': 'string'},
                        'server_info': {'type': 'object', 'optional': True}
                    }
                }
            },
            'chats': {
                'path': '/chats',
                'method': 'GET',
                'description': 'Get user chats with filtering and pagination',
                'authentication_required': True,
                'parameters': {
                    'limit': {'type': 'integer', 'location': 'query', 'default': 50, 'max': 100},
                    'offset': {'type': 'integer', 'location': 'query', 'default': 0},
                    'search': {'type': 'string', 'location': 'query', 'description': 'Search term for chat titles'},
                    'sort': {'type': 'string', 'location': 'query', 'enum': ['created_at', 'updated_at', 'title'], 'default': 'updated_at'},
                    'order': {'type': 'string', 'location': 'query', 'enum': ['asc', 'desc'], 'default': 'desc'}
                },
                'response': {
                    'type': 'object',
                    'properties': {
                        'chats': {'type': 'array'},
                        'pagination': {'type': 'object'},
                        'filters': {'type': 'object'}
                    }
                }
            },
            'create_chat': {
                'path': '/chats',
                'method': 'POST',
                'description': 'Create a new chat',
                'authentication_required': True,
                'parameters': {
                    'title': {'type': 'string', 'location': 'body', 'optional': True},
                    'initial_message': {'type': 'string', 'location': 'body', 'optional': True},
                    'model': {'type': 'string', 'location': 'body', 'optional': True}
                },
                'response': {
                    'type': 'object',
                    'properties': {
                        'chat': {'type': 'object'}
                    }
                }
            },
            'chat_details': {
                'path': '/chats/{chat_id}',
                'method': 'GET',
                'description': 'Get detailed chat information',
                'authentication_required': True,
                'parameters': {
                    'chat_id': {'type': 'integer', 'location': 'path'}
                },
                'response': {
                    'type': 'object',
                    'properties': {
                        'chat': {'type': 'object', 'includes': ['messages', 'statistics']}
                    }
                }
            },
            'export_chat': {
                'path': '/chats/{chat_id}/export',
                'method': 'GET',
                'description': 'Export chat in various formats',
                'authentication_required': True,
                'parameters': {
                    'chat_id': {'type': 'integer', 'location': 'path'},
                    'format': {'type': 'string', 'location': 'query', 'enum': ['json', 'markdown', 'text'], 'default': 'json'},
                    'include_metadata': {'type': 'boolean', 'location': 'query', 'default': True}
                },
                'response': {
                    'type': 'object',
                    'properties': {
                        'export': {'type': 'string or object', 'description': 'Exported data'},
                        'format': {'type': 'string'},
                        'content_type': {'type': 'string'},
                        'filename': {'type': 'string'}
                    }
                }
            },
            'user_profile': {
                'path': '/user/profile',
                'method': 'GET',
                'description': 'Get current user profile with statistics',
                'authentication_required': True,
                'parameters': {},
                'response': {
                    'type': 'object',
                    'properties': {
                        'user': {'type': 'object'},
                        'settings': {'type': 'object'},
                        'statistics': {'type': 'object'}
                    }
                }
            },
            'user_settings': {
                'path': '/user/settings',
                'method': 'GET',
                'description': 'Get current user settings',
                'authentication_required': True,
                'parameters': {},
                'response': {
                    'type': 'object',
                    'properties': {
                        'settings': {'type': 'object'}
                    }
                }
            },
            'update_user_settings': {
                'path': '/user/settings',
                'method': 'PUT',
                'description': 'Update current user settings',
                'authentication_required': True,
                'parameters': {
                    'ollama_host': {'type': 'string', 'location': 'body', 'description': 'OLLAMA server URL'}
                },
                'response': {
                    'type': 'object',
                    'properties': {
                        'settings': {'type': 'object'}
                    }
                }
            },
            'user_preferences': {
                'path': '/user/preferences',
                'method': 'GET',
                'description': 'Get user preferences (placeholder for future features)',
                'authentication_required': True,
                'parameters': {},
                'response': {
                    'type': 'object',
                    'properties': {
                        'preferences': {'type': 'object'}
                    }
                }
            },
            'user_activity': {
                'path': '/user/activity',
                'method': 'GET',
                'description': 'Get user activity summary',
                'authentication_required': True,
                'parameters': {},
                'response': {
                    'type': 'object',
                    'properties': {
                        'recent_activity': {'type': 'object'},
                        'most_recent_chats': {'type': 'array'}
                    }
                }
            }
        },
        'response_format': {
            'description': 'All v1 endpoints return standardized responses',
            'success_response': {
                'success': {'type': 'boolean', 'description': 'Always true for successful responses'},
                'timestamp': {'type': 'string', 'format': 'datetime'},
                'request_id': {'type': 'string', 'description': 'Unique request identifier'},
                'version': {'type': 'string', 'description': 'API version (v1)'},
                'data': {'type': 'any', 'description': 'Response data'},
                'message': {'type': 'string', 'optional': True, 'description': 'Optional success message'}
            },
            'error_response': {
                'success': {'type': 'boolean', 'description': 'Always false for error responses'},
                'timestamp': {'type': 'string', 'format': 'datetime'},
                'request_id': {'type': 'string', 'description': 'Unique request identifier'},
                'version': {'type': 'string', 'description': 'API version (v1)'},
                'error': {
                    'type': 'object',
                    'properties': {
                        'type': {'type': 'string', 'description': 'Error type'},
                        'message': {'type': 'string', 'description': 'Error message'},
                        'details': {'type': 'object', 'description': 'Additional error details'}
                    }
                }
            }
        },
        'rate_limits': {
            'description': 'API endpoints have different rate limits',
            'models_endpoints': '50 per minute',
            'connection_test': '15 per minute',
            'chats_list': '100 per minute',
            'chat_create': '20 per minute',
            'default': '200 per day, 50 per hour'
        },
        'changes_from_legacy': {
            'description': 'Key differences from legacy /api/* endpoints',
            'changes': [
                'Standardized response format with success/error structure',
                'Request tracking with unique request IDs',
                'Enhanced error handling with error types and details',
                'Improved rate limits for better performance',
                'Additional metadata and enhanced features',
                'Backward compatibility maintained for existing clients'
            ]
        }
    }
    
    return api_response(
        data=documentation,
        message="API v1 documentation retrieved successfully"
    )


@api_v1_bp.route('/docs/openapi')
@track_request()
def openapi_schema():
    """
    Get basic OpenAPI-style schema for API v1.
    
    This is a simplified OpenAPI schema for documentation purposes.
    """
    openapi_spec = {
        'openapi': '3.0.3',
        'info': {
            'title': 'OLLAMA Chat API v1',
            'version': '1.0.0',
            'description': 'Enhanced API for OLLAMA Chat application with proper versioning and improved features'
        },
        'servers': [
            {
                'url': '/api/v1',
                'description': 'API v1 base URL'
            }
        ],
        'security': [
            {
                'sessionAuth': []
            }
        ],
        'components': {
            'securitySchemes': {
                'sessionAuth': {
                    'type': 'apiKey',
                    'in': 'cookie',
                    'name': 'session'
                }
            },
            'schemas': {
                'StandardResponse': {
                    'type': 'object',
                    'properties': {
                        'success': {'type': 'boolean'},
                        'timestamp': {'type': 'string', 'format': 'date-time'},
                        'request_id': {'type': 'string'},
                        'version': {'type': 'string'},
                        'data': {'type': 'object'},
                        'message': {'type': 'string'}
                    },
                    'required': ['success', 'timestamp', 'request_id', 'version']
                },
                'ErrorResponse': {
                    'type': 'object',
                    'properties': {
                        'success': {'type': 'boolean', 'enum': [False]},
                        'timestamp': {'type': 'string', 'format': 'date-time'},
                        'request_id': {'type': 'string'},
                        'version': {'type': 'string'},
                        'error': {
                            'type': 'object',
                            'properties': {
                                'type': {'type': 'string'},
                                'message': {'type': 'string'},
                                'details': {'type': 'object'}
                            }
                        }
                    }
                }
            }
        },
        'paths': {
            '/health': {
                'get': {
                    'summary': 'Health check',
                    'description': 'Get system health status',
                    'security': [],
                    'responses': {
                        '200': {
                            'description': 'Health check result',
                            'content': {
                                'application/json': {
                                    'schema': {'$ref': '#/components/schemas/StandardResponse'}
                                }
                            }
                        }
                    }
                }
            },
            '/models': {
                'get': {
                    'summary': 'Get OLLAMA models',
                    'description': 'Get available OLLAMA models with enhanced metadata',
                    'responses': {
                        '200': {
                            'description': 'List of models',
                            'content': {
                                'application/json': {
                                    'schema': {'$ref': '#/components/schemas/StandardResponse'}
                                }
                            }
                        }
                    }
                }
            }
        },
        'note': 'This is a simplified OpenAPI spec. Full specification would include all endpoints with detailed schemas.'
    }
    
    return api_response(
        data=openapi_spec,
        message="OpenAPI schema retrieved successfully"
    )