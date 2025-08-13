"""
Enhanced logging configuration for OLLAMA Chat.

Provides structured logging with request IDs, performance metrics,
and improved debugging capabilities.
"""

import logging
import logging.handlers
import json
import time
from datetime import datetime
from flask import g, request, has_request_context
import os


class StructuredFormatter(logging.Formatter):
    """
    Custom log formatter that outputs structured JSON logs.
    
    Includes request context, timing information, and structured data.
    """
    
    def format(self, record):
        """Format log record as structured JSON."""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add request context if available
        if has_request_context():
            log_data['request'] = {
                'id': getattr(g, 'request_id', None),
                'method': request.method,
                'path': request.path,
                'endpoint': getattr(g, 'endpoint', None),
                'remote_addr': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', 'Unknown')[:100],  # Truncate long user agents
                'duration_ms': round((getattr(g, 'request_duration', 0)) * 1000, 2) if hasattr(g, 'request_duration') else None
            }
            
            # Add user context if available
            try:
                from flask_login import current_user
                if current_user and current_user.is_authenticated:
                    log_data['user'] = {
                        'id': current_user.id,
                        'email': current_user.email
                    }
            except (ImportError, AttributeError):
                pass
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
        
        # Add extra fields from the log record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'stack_info', 'exc_info', 'exc_text']:
                extra_fields[key] = value
        
        if extra_fields:
            log_data['extra'] = extra_fields
        
        return json.dumps(log_data, ensure_ascii=False)


class RequestContextFilter(logging.Filter):
    """
    Logging filter that adds request context to log records.
    """
    
    def filter(self, record):
        """Add request context to log record."""
        if has_request_context():
            record.request_id = getattr(g, 'request_id', 'unknown')
            record.request_method = request.method
            record.request_path = request.path
            record.remote_addr = request.remote_addr
        else:
            record.request_id = 'no-request'
            record.request_method = 'N/A'
            record.request_path = 'N/A'
            record.remote_addr = 'N/A'
        
        return True


def setup_enhanced_logging(app):
    """
    Configure enhanced logging for the Flask application.
    
    Args:
        app: Flask application instance
    """
    
    # Get log level from environment
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove default handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler (only if explicitly enabled)
    # By default, logs only go to files. Set LOG_TO_CONSOLE=true to enable console output
    if os.environ.get('LOG_TO_CONSOLE', 'false').lower() == 'true':
        console_handler = logging.StreamHandler()
        if os.environ.get('LOG_FORMAT', 'structured').lower() == 'structured':
            console_handler.setFormatter(StructuredFormatter())
        else:
            # Simple format for development
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s [%(levelname)s] [%(request_id)s] %(name)s: %(message)s'
            ))
        console_handler.addFilter(RequestContextFilter())
        console_handler.setLevel(logging.INFO)
        root_logger.addHandler(console_handler)
        app.logger.info("Console logging enabled via LOG_TO_CONSOLE=true")
    else:
        # Inform user that logs are going to files
        print(f"[OLLAMA Chat] Logs are being written to: {logs_dir}/")
        print(f"[OLLAMA Chat] To enable console logging, set LOG_TO_CONSOLE=true")
    
    # Rotating file handler for application logs
    # Max 10MB per file, keep 5 backup files (50MB total)
    app_log_handler = logging.handlers.RotatingFileHandler(
        os.path.join(logs_dir, 'ollama_chat.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    app_log_handler.setFormatter(StructuredFormatter())
    app_log_handler.addFilter(RequestContextFilter())
    app_log_handler.setLevel(logging.INFO)
    root_logger.addHandler(app_log_handler)
    
    # Separate rotating error log
    # Max 5MB per file, keep 3 backup files (15MB total)
    error_log_handler = logging.handlers.RotatingFileHandler(
        os.path.join(logs_dir, 'errors.log'),
        maxBytes=5*1024*1024,   # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_log_handler.setFormatter(StructuredFormatter())
    error_log_handler.addFilter(RequestContextFilter())
    error_log_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_log_handler)
    
    # Access log for web requests (separate from application log)
    # Max 20MB per file, keep 7 backup files (140MB total)
    access_log_handler = logging.handlers.RotatingFileHandler(
        os.path.join(logs_dir, 'access.log'),
        maxBytes=20*1024*1024,  # 20MB
        backupCount=7,
        encoding='utf-8'
    )
    access_log_handler.setFormatter(StructuredFormatter())
    access_log_handler.addFilter(RequestContextFilter())
    access_log_handler.setLevel(logging.INFO)
    
    # Create dedicated logger for access logs
    access_logger = logging.getLogger('access')
    access_logger.addHandler(access_log_handler)
    access_logger.setLevel(logging.INFO)
    access_logger.propagate = False  # Don't propagate to root logger
    
    # Performance log for slow operations
    # Max 5MB per file, keep 3 backup files (15MB total)
    perf_log_handler = logging.handlers.RotatingFileHandler(
        os.path.join(logs_dir, 'performance.log'),
        maxBytes=5*1024*1024,   # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    perf_log_handler.setFormatter(StructuredFormatter())
    perf_log_handler.addFilter(RequestContextFilter())
    perf_log_handler.setLevel(logging.INFO)
    
    # Create dedicated logger for performance logs
    perf_logger = logging.getLogger('performance')
    perf_logger.addHandler(perf_log_handler)
    perf_logger.setLevel(logging.INFO)
    perf_logger.propagate = False  # Don't propagate to root logger
    
    # Configure Flask app logger
    app.logger.setLevel(log_level)
    
    # Configure specific loggers
    logging.getLogger('werkzeug').setLevel(logging.WARNING)  # Reduce Werkzeug noise
    logging.getLogger('urllib3').setLevel(logging.WARNING)  # Reduce urllib3 noise
    
    # Add request logging middleware
    @app.before_request
    def log_request_start():
        """Log the start of each request."""
        if not getattr(g, 'request_start_time', None):
            g.request_start_time = time.time()
        
        # Log to dedicated access logger
        access_logger = logging.getLogger('access')
        access_logger.info(
            f"Request started: {request.method} {request.path}",
            extra={
                'event': 'request_start',
                'method': request.method,
                'path': request.path,
                'query_string': request.query_string.decode('utf-8'),
                'content_length': request.content_length,
                'content_type': request.content_type
            }
        )
    
    @app.after_request
    def log_request_end(response):
        """Log the end of each request with timing and response info."""
        duration = time.time() - getattr(g, 'request_start_time', time.time())
        g.request_duration = duration
        
        # Safely get response size without triggering passthrough mode issues
        response_size = 0
        try:
            if hasattr(response, 'content_length') and response.content_length:
                response_size = response.content_length
            elif hasattr(response, 'get_data'):
                # Only try to get data if it's safe to do so
                try:
                    data = response.get_data(as_text=False)
                    response_size = len(data) if data else 0
                except (RuntimeError, AttributeError):
                    # Response is in passthrough mode or other issue
                    response_size = 0
        except Exception:
            response_size = 0
        
        # Log to dedicated access logger
        access_logger = logging.getLogger('access')
        access_logger.info(
            f"Request completed: {request.method} {request.path} -> {response.status_code}",
            extra={
                'event': 'request_end',
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'content_length': response.content_length,
                'duration_ms': round(duration * 1000, 2),
                'response_size': response_size
            }
        )
        
        # Log slow requests to performance log
        duration_ms = round(duration * 1000, 2)
        if duration_ms > 1000:  # Log requests slower than 1 second
            perf_logger = logging.getLogger('performance')
            perf_logger.warning(
                f"Slow request: {request.method} {request.path} took {duration_ms}ms",
                extra={
                    'event': 'slow_request',
                    'method': request.method,
                    'path': request.path,
                    'duration_ms': duration_ms,
                    'status_code': response.status_code,
                    'threshold_ms': 1000
                }
            )
        
        return response
    
    # Log configuration summary to files
    console_enabled = os.environ.get('LOG_TO_CONSOLE', 'false').lower() == 'true'
    app.logger.info(
        "Enhanced logging configured successfully",
        extra={
            'event': 'logging_init',
            'log_level': log_level,
            'structured_format': os.environ.get('LOG_FORMAT', 'structured').lower() == 'structured',
            'console_logging': console_enabled,
            'log_files': {
                'application': 'ollama_chat.log (10MB, 5 backups)',
                'access': 'access.log (20MB, 7 backups)',
                'errors': 'errors.log (5MB, 3 backups)',
                'performance': 'performance.log (5MB, 3 backups)'
            }
        }
    )
    
    # Print a simple startup message to console
    if not console_enabled:
        print("[OLLAMA Chat] Application started - logs are being written to files")
        print(f"[OLLAMA Chat] Monitor logs: tail -f {logs_dir}/ollama_chat.log")
        print(f"[OLLAMA Chat] Monitor access: tail -f {logs_dir}/access.log")


def get_logger(name):
    """
    Get a logger with enhanced configuration.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class RequestLogger:
    """
    Context manager for structured request logging.
    
    Usage:
        with RequestLogger('operation_name') as logger:
            logger.info("Operation started")
            # ... do work ...
            logger.info("Operation completed")
    """
    
    def __init__(self, operation, logger_name=None):
        self.operation = operation
        self.logger = get_logger(logger_name or __name__)
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.logger.info(
            f"Starting operation: {self.operation}",
            extra={'event': 'operation_start', 'operation': self.operation}
        )
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type:
            self.logger.error(
                f"Operation failed: {self.operation}",
                extra={
                    'event': 'operation_error',
                    'operation': self.operation,
                    'duration_ms': round(duration * 1000, 2),
                    'error_type': exc_type.__name__,
                    'error_message': str(exc_val)
                },
                exc_info=True
            )
        else:
            self.logger.info(
                f"Operation completed: {self.operation}",
                extra={
                    'event': 'operation_end',
                    'operation': self.operation,
                    'duration_ms': round(duration * 1000, 2)
                }
            )


# Convenience functions for common logging patterns
def log_api_call(endpoint, method, user_id=None, **kwargs):
    """Log an API call with structured data."""
    logger = get_logger('api')
    logger.info(
        f"API call: {method} {endpoint}",
        extra={
            'event': 'api_call',
            'endpoint': endpoint,
            'method': method,
            'user_id': user_id,
            **kwargs
        }
    )


def log_database_operation(operation, table, user_id=None, **kwargs):
    """Log a database operation with structured data."""
    logger = get_logger('database')
    logger.info(
        f"Database operation: {operation} on {table}",
        extra={
            'event': 'database_operation',
            'operation': operation,
            'table': table,
            'user_id': user_id,
            **kwargs
        }
    )


def log_external_service_call(service, operation, response_time=None, **kwargs):
    """Log an external service call with structured data."""
    logger = get_logger('external')
    logger.info(
        f"External service call: {service}.{operation}",
        extra={
            'event': 'external_service_call',
            'service': service,
            'operation': operation,
            'response_time_ms': response_time,
            **kwargs
        }
    )
    
    # Also log to performance logger if it's slow
    if response_time and response_time > 500:  # Slow external service call
        perf_logger = logging.getLogger('performance')
        perf_logger.warning(
            f"Slow external service: {service}.{operation} took {response_time}ms",
            extra={
                'event': 'slow_external_service',
                'service': service,
                'operation': operation,
                'response_time_ms': response_time,
                'threshold_ms': 500,
                **kwargs
            }
        )


def log_performance_metric(operation, duration_ms, **kwargs):
    """Log a performance metric to the performance log."""
    perf_logger = logging.getLogger('performance')
    perf_logger.info(
        f"Performance metric: {operation} took {duration_ms}ms",
        extra={
            'event': 'performance_metric',
            'operation': operation,
            'duration_ms': duration_ms,
            **kwargs
        }
    )


def log_cache_operation(cache_type, operation, hit=None, **kwargs):
    """Log cache operations for monitoring cache efficiency."""
    logger = get_logger('cache')
    logger.info(
        f"Cache {operation}: {cache_type}",
        extra={
            'event': 'cache_operation',
            'cache_type': cache_type,
            'operation': operation,
            'hit': hit,
            **kwargs
        }
    )