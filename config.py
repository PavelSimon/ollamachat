"""
Configuration settings for OLLAMA Chat application
"""
import os
import secrets
import warnings
from datetime import timedelta

def generate_secret_key():
    """Generate a secure secret key if none is provided"""
    return secrets.token_hex(32)

def validate_production_config():
    """Validate critical production configuration"""
    if os.environ.get('FLASK_ENV') == 'production':
        if not os.environ.get('SECRET_KEY'):
            raise ValueError(
                "SECRET_KEY environment variable must be set in production. "
                "Generate one with: python -c 'import secrets; print(secrets.token_hex(32))'"
            )
        if not os.environ.get('DATABASE_URL'):
            warnings.warn(
                "DATABASE_URL not set in production, using SQLite which is not recommended for production"
            )

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or generate_secret_key()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # SQLite optimizations
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,  # Recycle connections every 5 minutes
        'connect_args': {
            'check_same_thread': False,
            'timeout': 30,
        }
    }
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    
    # Application Constants
    MAX_MESSAGE_LENGTH = 10000
    MAX_TITLE_LENGTH = 200
    MAX_BULK_DELETE_LIMIT = 100
    MAX_URL_LENGTH = 500
    DEFAULT_MODEL_NAME = 'gpt-oss:20b'
    CONVERSATION_HISTORY_LIMIT = 10
    AUTO_TITLE_MESSAGE_LIMIT = 2
    AUTO_TITLE_MAX_LENGTH = 50
    AUTH_TIMING_DELAY = 0.1  # Minimum delay in seconds to prevent timing attacks

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///chat.db'
    
class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///chat.db'
    
    # Security settings for production
    SESSION_COOKIE_SECURE = True  # Requires HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'  # More restrictive for production
    WTF_CSRF_ENABLED = True
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    def __init__(self):
        # Validate production configuration on initialization
        validate_production_config()

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}