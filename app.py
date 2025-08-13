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
    return User.query.get(int(user_id))

# Make limiter available to other modules
def get_limiter():
    return limiter

# Register blueprints
from routes.auth import auth_bp
from routes.main import main_bp
from routes.settings import settings_bp
from routes.api import api_bp
from routes.chat import chat_bp

app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(api_bp)
app.register_blueprint(chat_bp)

# Apply rate limiting to specific endpoints after blueprint registration
# Chat endpoints
limiter.limit("10 per minute")(app.view_functions['chat.api_chats'])
limiter.limit("20 per minute")(app.view_functions['chat.api_send_message'])

# API endpoints  
limiter.limit("30 per minute")(app.view_functions['api.get_models'])
limiter.limit("10 per minute")(app.view_functions['api.test_connection'])

# Auth endpoints (more restrictive)
limiter.limit("5 per minute")(app.view_functions['auth.login'])
limiter.limit("3 per minute")(app.view_functions['auth.register'])

# Settings endpoints
if 'settings.api_settings' in app.view_functions:
    limiter.limit("10 per minute")(app.view_functions['settings.api_settings'])

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Endpoint nenájdený'}), 404
    return "Stránka nenájdená", 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Interná chyba servera'}), 500
    return "Interná chyba servera", 500

@app.errorhandler(403)
def forbidden_error(error):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Prístup zamietnutý'}), 403
    return "Prístup zamietnutý", 403

@app.errorhandler(RateLimitExceeded)
def ratelimit_handler(e):
    """Handle rate limit exceeded errors"""
    if request.path.startswith('/api/'):
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': f'Prekročený limit požiadaviek: {e.description}',
            'retry_after': e.retry_after
        }), 429
    return f"Rate limit exceeded: {e.description}", 429

# Security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    if app.config.get('SESSION_COOKIE_SECURE'):
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Setup logging
if not app.debug:
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)
    app.logger.info('OLLAMA Chat startup')

def init_db():
    """Initialize database with tables"""
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")

if __name__ == '__main__':
    init_db()
    app.run(debug=True)