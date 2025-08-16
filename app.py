from flask import Flask, jsonify, request
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_limiter.errors import RateLimitExceeded
import os
import logging
from models import db, User

# Initialize Flask app
app = Flask(__name__)

# Configuration
from config import config, validate_production_config
config_name = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config[config_name])

# Validate production configuration if needed
if config_name == 'production':
    validate_production_config()

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=os.environ.get('RATELIMIT_STORAGE_URL', 'memory://'),
    headers_enabled=True
)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Make limiter available to other modules
def get_limiter():
    return limiter

# Register blueprints
from routes.auth import auth_bp
from routes.main import main_bp
from routes.settings import settings_bp
from routes.chat import chat_bp

# Import API routes
from routes.api import api_bp  # Legacy API from routes/api.py

app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(api_bp)  # API endpoints
app.register_blueprint(chat_bp)

# Apply rate limiting to specific endpoints after blueprint registration
# Chat endpoints
limiter.limit("10 per minute")(app.view_functions['chat.api_chats'])
limiter.limit("20 per minute")(app.view_functions['chat.api_send_message'])
limiter.limit("5 per minute")(app.view_functions['chat.api_bulk_delete_chats'])  # Restrictive for bulk operations

# Legacy API endpoints  
limiter.limit("30 per minute")(app.view_functions['api.get_models'])
limiter.limit("10 per minute")(app.view_functions['api.test_connection'])

# Removed unused v1 API rate limiting

# Auth endpoints (more restrictive for security)
limiter.limit("5 per minute")(app.view_functions['auth.login'])
limiter.limit("10 per hour")(app.view_functions['auth.login'])  # Additional hourly limit
limiter.limit("3 per minute")(app.view_functions['auth.register'])
limiter.limit("5 per hour")(app.view_functions['auth.register'])  # Additional hourly limit

# Settings endpoints
if 'settings.api_settings' in app.view_functions:
    limiter.limit("10 per minute")(app.view_functions['settings.api_settings'])

# Register standardized error handlers
from error_handlers import register_error_handlers, ErrorHandler
register_error_handlers(app)

@app.errorhandler(RateLimitExceeded)
def ratelimit_handler(e):
    """Handle rate limit exceeded errors"""
    if request.path.startswith('/api/'):
        return ErrorHandler.rate_limit_error(
            f'Prekročený limit požiadaviek: {e.description}'
        )
    return f"Rate limit exceeded: {e.description}", 429

@app.errorhandler(403)
def forbidden_error(error):
    """Handle forbidden access errors"""
    if request.path.startswith('/api/'):
        return ErrorHandler.forbidden("Prístup zamietnutý")
    return "Prístup zamietnutý", 403

# Custom 500 handler with rollback
@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors with database rollback"""
    db.session.rollback()
    if request.path.startswith('/api/'):
        return ErrorHandler.internal_error(
            Exception("Internal server error"),
            "Global error handler",
            "Interná chyba servera"
        )
    return "Interná chyba servera", 500

# Security headers
@app.after_request
def add_security_headers(response):
    # Basic security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    
    # Content Security Policy
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    response.headers['Content-Security-Policy'] = csp
    
    # HSTS for production with HTTPS
    if app.config.get('SESSION_COOKIE_SECURE'):
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
    
    return response

# Setup enhanced logging
from enhanced_logging import setup_enhanced_logging
setup_enhanced_logging(app)

def init_db():
    """Initialize database with tables"""
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")

if __name__ == '__main__':
    init_db()
    # Only enable debug mode in development environment
    debug_mode = os.environ.get('FLASK_ENV', 'production') == 'development'
    app.run(debug=debug_mode)