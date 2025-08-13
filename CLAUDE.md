# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OLLAMA Chat is a Flask-based web application that provides a chat interface for communicating with local OLLAMA AI models. The application features user authentication, chat management, and real-time AI conversations.

**Key Technologies:**
- Flask web framework with blueprints architecture
- SQLite database with SQLAlchemy ORM
- uv for Python dependency management (requires Python 3.13+)
- Flask-Login for user session management
- Flask-WTF for forms and CSRF protection
- Vanilla JavaScript frontend with markdown rendering

## Development Commands

**Environment Setup:**
```bash
# Copy and configure environment
cp .env.example .env

# Install dependencies
uv sync

# Install with development dependencies
uv sync --dev

# Start development server
uv run app.py

# Alternative with virtual environment
uv venv && source .venv/bin/activate  # .venv\Scripts\activate on Windows
uv pip install -e .
python app.py
```

**Testing:**
```bash
# Run all tests
uv run pytest

# Run integration tests with real OLLAMA server
uv run python tests/test_ollama_integration.py

# Run integration tests with custom server
uv run python tests/test_ollama_integration.py http://your-server:11434
```

**Configuration Validation:**
```bash
# Validate environment configuration
uv run python validate_config.py

# Generate secure SECRET_KEY
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"

# Migrate database (add performance indexes)
uv run python migrate_database.py
```

**Production Deployment:**
```bash
# Production with gunicorn
uv sync --extra production
uv run gunicorn --bind 0.0.0.0:5000 --workers 4 app:app

# Docker deployment
cp .env.example .env  # Configure first
docker-compose up -d

# Database initialization
uv run python -c "from app import init_db; init_db()"
```

## Architecture Overview

### Application Structure
```
app.py                 # Flask application factory, blueprint registration
config.py              # Environment-based configuration classes
models.py              # SQLAlchemy database models
database_operations.py # Database operation abstractions
ollama_client.py       # OLLAMA API client wrapper
forms.py              # WTForms form definitions
routes/               # Flask blueprints for different functionality
```

### Database Design
The application uses four main models:
- **User**: Authentication and user management with bcrypt password hashing
- **UserSettings**: Per-user configuration (OLLAMA server host)  
- **Chat**: Chat conversation containers with auto-generated titles
- **Message**: Individual messages with user/AI distinction and model tracking

### Blueprint Organization
- `auth_bp`: User registration, login, logout (`routes/auth.py`)
- `main_bp`: Index and chat page routing (`routes/main.py`)  
- `chat_bp`: Chat CRUD operations and AI message handling (`routes/chat.py`)
- `api_bp`: OLLAMA server connection testing and model listing (`routes/api.py`)
- `settings_bp`: User settings management (`routes/settings.py`)

### Frontend Architecture
- **Static Assets**: Organized in `static/css/` and `static/js/`
- **Templates**: Jinja2 templates with base template inheritance
- **JavaScript**: Vanilla JS with fetch API for AJAX calls
- **Markdown Rendering**: Custom client-side implementation with XSS protection
- **Real-time UI**: Manual refresh pattern (no WebSockets currently)

## Key Configuration Points

### Environment Variables (Required)
- `SECRET_KEY`: Cryptographic key for sessions/CSRF (auto-generated in development)
- `FLASK_ENV`: Application environment (`development`/`production`/`testing`)
- `DATABASE_URL`: Database connection string (defaults to SQLite)
- `DEFAULT_OLLAMA_HOST`: Default OLLAMA server URL (defaults to `http://localhost:11434`)

### Security Considerations
- Production requires explicit SECRET_KEY in environment
- CSRF protection enabled by default via Flask-WTF
- Session cookies configured with security headers
- Input validation through WTForms
- XSS protection in markdown rendering

### OLLAMA Integration
- Each user can configure their own OLLAMA server URL
- Connection testing endpoint available at `/api/test-connection`
- Model discovery via `/api/models` endpoint
- Extended timeouts (120s) for slow model responses
- Conversation context maintained (last 10 messages)

## Database Operations Pattern

The codebase uses a clean separation with operation classes:
```python
# User operations
user = UserOperations.create_user(email, password)
user = UserOperations.authenticate_user(email, password)

# Chat operations  
chat = ChatOperations.create_chat(user_id, title=None)
chats = ChatOperations.get_user_chats(user_id)

# Message operations
message = MessageOperations.add_message(chat_id, content, is_user, model_name)
messages = MessageOperations.get_chat_messages(chat_id, user_id)

# Settings operations
settings = SettingsOperations.get_user_settings(user_id)
SettingsOperations.update_ollama_host(user_id, new_host)
```

## Testing Strategy

**Unit Tests**: Mock-based testing in `tests/test_*.py`
- Database operations testing
- Authentication flow testing  
- OLLAMA client mocking
- Settings management testing

**Integration Tests**: Real OLLAMA server testing in `test_ollama_integration.py`
- Requires running OLLAMA server
- Tests actual model communication
- Configurable OLLAMA server endpoint

## Common Development Patterns

### Adding New Routes
1. Create route function in appropriate blueprint file
2. Add necessary imports and decorators (@login_required for protected routes)
3. Use database operations classes rather than direct SQLAlchemy calls
4. Return JSON for API endpoints, render templates for pages

### Database Schema Changes
1. Modify model definitions in `models.py`
2. No formal migration system - database recreated on startup in development
3. Production deployments require manual schema updates

### Frontend JavaScript Updates
1. Follow existing fetch() pattern for API calls
2. Use manual error handling and user feedback
3. Update `formatMarkdown()` function for content rendering changes
4. Maintain CSRF token handling in forms

### OLLAMA Client Extensions
1. Extend `OllamaClient` class in `ollama_client.py`
2. Add appropriate error handling with `OllamaConnectionError`
3. Use per-request timeouts rather than global timeouts
4. Test with both unit tests (mocked) and integration tests (real server)

## Improvement Implementation Priority

When working on enhancements, follow this priority order:

### Phase 1: Critical Security & Performance (1-2 weeks) - ✅ COMPLETED
1. ✅ **Input Validation**: Added comprehensive Marshmallow validation to all API endpoints
2. ✅ **Database Indexes**: Added composite indexes on `messages` and `chats` tables
3. ✅ **Rate Limiting**: Implemented Flask-Limiter with endpoint-specific rate limits

### Phase 2: Code Quality & Reliability (2-4 weeks) - ✅ COMPLETED
1. ✅ **Error Handling**: Implemented centralized ErrorHandler class with standardized JSON error responses
2. ✅ **Connection Pooling**: Added OLLAMA client connection pool with LRU eviction and health checking
3. ✅ **Response Caching**: Implemented TTL-based caching for model lists with 5-minute cache duration

### Phase 3: Architecture & UX Enhancements (1-3 months) - ✅ COMPLETED
1. ✅ **API Versioning**: Implemented `/api/v1/` namespace with enhanced endpoints and request tracking
2. ✅ **Enhanced Logging**: Added structured JSON logging with file rotation and performance monitoring
3. ✅ **Health Monitoring**: Implemented comprehensive health check endpoints with system metrics
4. ✅ **OLLAMA Version Display**: Added real-time OLLAMA server version information in chat interface
5. **Real-time Features**: WebSocket support for live chat updates  
6. **Advanced Features**: Chat export, search, categorization

## Recent Implementations (Phase 3 Completed)

### API Versioning System (`/api/v1/`)
- **Structure**: Created versioned API namespace in `routes/api_versions/v1/`
- **Endpoints**: Enhanced models, system health, chat management, and user profile endpoints
- **Features**: Request tracking, structured responses, comprehensive error handling
- **Monitoring**: Built-in performance metrics and request correlation IDs

### Enhanced Logging System
- **Implementation**: `enhanced_logging.py` with structured JSON logging
- **Features**: File rotation (10MB app logs, 20MB access logs), request correlation, performance tracking
- **Storage**: Organized in `logs/` directory with automatic cleanup and monitoring tools
- **Configuration**: Environment-controlled console output via `LOG_TO_CONSOLE`

### Connection Pooling & Caching
- **Pool Manager**: `ollama_pool.py` with thread-safe LRU eviction and health checking
- **Response Cache**: `response_cache.py` with TTL-based caching and decorator pattern
- **Performance**: Reduced OLLAMA API calls and improved response times

### OLLAMA Version Integration
- **Backend**: Enhanced `ollama_client.py` with `get_version()` method
- **API**: Updated `/api/models` endpoint to include version information
- **Frontend**: Real-time version display in compact layout (167px) under model selector
- **Layout**: Vertical stacking in chat header with consistent styling

### Error Handling Standardization
- **System**: Centralized `error_handlers.py` with structured JSON error responses
- **Features**: Error IDs, timestamps, request correlation, and user-friendly messages
- **Integration**: Applied across all routes with backward compatibility

## Production Considerations

- SQLite suitable for small deployments only
- Use gunicorn for production WSGI serving
- Configure proper logging levels via LOG_LEVEL environment variable
- HTTPS required for secure session cookies (SESSION_COOKIE_SECURE=true)
- Consider connection pooling for high-traffic scenarios

## Known Limitations

- No real-time updates (requires manual refresh)
- No user chat sharing or collaboration features  
- SQLite not suitable for high-concurrency production use
- No API rate limiting implemented
- No user data export/import functionality

## Critical Technical Debt & Improvements

### Security Issues (HIGH PRIORITY)
- ✅ **Input Sanitization**: Implemented comprehensive Marshmallow validation for all API endpoints
- ✅ **Rate Limiting**: Added Flask-Limiter with endpoint-specific limits (20/min for messages, 5/min for auth)
- **Content Security Policy**: Missing CSP headers for XSS protection

### Performance Bottlenecks
- ✅ **Database Indexes**: Added composite indexes on `messages.chat_id+created_at` and `chats.user_id+updated_at`
- ✅ **Connection Pooling**: Implemented OLLAMA client connection pool with LRU eviction and health checking
- ✅ **Response Caching**: Added TTL-based caching for model lists with 5-minute cache duration

### Code Quality Issues
- ✅ **Error Handling**: Implemented centralized ErrorHandler class with standardized JSON error responses
- **Type Hints**: Incomplete coverage - `ollama_client.py` has types, others don't
- **Configuration**: Some hardcoded values still exist - centralize all config in `config.py`

### Architectural Gaps
- ✅ **API Versioning**: Implemented `/api/v1/` namespace with enhanced endpoints and request tracking
- **Database Migrations**: No formal migration system - consider Flask-Migrate for production
- ✅ **Logging**: Implemented structured JSON logging with file rotation, request IDs, and performance monitoring

## Files to Modify for Common Tasks

**Adding Authentication Features**: `routes/auth.py`, `forms.py`, `models.py`
**Database Schema Changes**: `models.py`, `database_operations.py`  
**OLLAMA Integration**: `ollama_client.py`, `routes/api.py`, `routes/chat.py`
**Frontend UI**: `templates/*.html`, `static/css/*.css`, `static/js/*.js`
**Configuration**: `config.py`, `.env.example`
**Testing**: `tests/test_*.py`
**API Versioning**: `routes/api_versions/v1/*.py`
**Logging & Monitoring**: `enhanced_logging.py`, `logs/`
**Error Handling**: `error_handlers.py`
**Performance**: `ollama_pool.py`, `response_cache.py`

## New Files Added (Phase 3 Implementation)

### Core Infrastructure
- `enhanced_logging.py` - Structured JSON logging with file rotation
- `error_handlers.py` - Centralized error handling with standardized responses
- `ollama_pool.py` - OLLAMA client connection pooling with health checking
- `response_cache.py` - TTL-based response caching system

### API Versioning Structure
- `routes/api_versions/` - Directory for versioned API endpoints
- `routes/api_versions/v1/base.py` - Base framework for v1 API with request tracking
- `routes/api_versions/v1/models.py` - Enhanced model endpoints with metadata
- `routes/api_versions/v1/system.py` - Health checks and system monitoring
- `routes/api_versions/v1/chat.py` - Advanced chat management features
- `routes/api_versions/v1/users.py` - User profile and settings management

### Logging Infrastructure
- `logs/` - Log storage directory with automatic rotation
- `logs/README.md` - Documentation for log management
- `logs/monitor.py` - Log viewing and monitoring utilities
- `.gitignore` - Updated to exclude log files from version control

## Key Files Needing Attention

Based on the improvements analysis:

**High Priority Fixes:**
- ✅ `routes/api.py` - Standardized error handling with ErrorHandler class
- ✅ `models.py` - Added database indexes on `messages.chat_id+created_at`, `chats.user_id+updated_at`
- ✅ `static/js/chat.js:55-90` - Model loading enhanced with version display and caching
- `static/js/chat.js:164` - Markdown rendering could use proper library instead of custom implementation

**Security Enhancements:**
- ✅ All route files in `routes/` - Added comprehensive input validation and rate limiting
- `app.py` - Add CSP headers to security headers function
- ✅ `config.py` - Improved with secure SECRET_KEY generation

**Performance Optimizations:**
- ✅ `ollama_client.py` - Implemented connection pooling with `ollama_pool.py`
- ✅ `routes/api.py` and `routes/chat.py` - Added TTL-based response caching with `response_cache.py`