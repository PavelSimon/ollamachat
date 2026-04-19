# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OLLAMA Chat is a Flask-based web application that provides a chat interface for communicating with local OLLAMA AI models. It has user authentication, per-user chat management, and synchronous (non-streaming) AI conversations.

**Key Technologies:**
- Flask 2.3 with blueprints architecture
- SQLite (dev) via SQLAlchemy 3.0 ORM — PostgreSQL supported via `DATABASE_URL`
- `uv` for Python dependency management (requires Python 3.13+)
- Flask-Login for session management
- Flask-WTF + WTForms for forms and CSRF protection
- Flask-Limiter for rate limiting (memory backend by default)
- Flask-Migrate (Alembic) for schema evolution
- Werkzeug password hashing (scrypt/pbkdf2 depending on Werkzeug version)
- Vanilla JavaScript frontend with custom markdown rendering

See `DEVELOPMENT_PLAN.md` for the active improvement plan.

## Development Commands

**Environment Setup:**
```bash
cp .env.example .env                # configure environment
uv sync                             # install dependencies
uv sync --dev                       # include dev deps (pytest, watchdog)
uv run app.py                       # start dev server
```

**Testing:**
```bash
uv run pytest                                            # all unit tests
uv run python tests/test_ollama_integration.py          # real OLLAMA server
uv run python tests/test_ollama_integration.py URL      # custom server
```

**Configuration & maintenance:**
```bash
uv run python validate_config.py                         # validate env
python -c "import secrets; print(secrets.token_hex(32))" # generate SECRET_KEY
uv run python migrate_database.py                        # apply index migrations
```

**Production:**
```bash
uv sync --extra production
uv run gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
# or:
docker-compose up -d
```

## Architecture Overview

### Top-level layout
```
app.py                    # Flask app factory, blueprint registration, security headers
config.py                 # Env-based config (Development/Production/Testing)
models.py                 # SQLAlchemy models (User, UserSettings, Chat, Message)
database_operations.py    # CRUD abstraction classes
ollama_client.py          # OLLAMA HTTP client (context-managed requests.Session)
error_handlers.py         # Centralized ErrorHandler + StandardError
enhanced_logging.py       # Structured JSON logging with rotation
rate_limiting.py          # Flask-Limiter wrapper with predefined limits
forms.py                  # WTForms definitions
validate_config.py        # Env validator
migrate_database.py       # One-shot index migration script
routes/                   # Flask blueprints (auth, main, chat, settings, api)
templates/ · static/      # Jinja2 templates + vanilla JS/CSS
tests/                    # pytest unit + integration tests
logs/                     # Rotated JSON logs (app, access, errors, performance)
```

### Blueprints
| Blueprint | File | Purpose |
|-----------|------|---------|
| `auth_bp` | `routes/auth.py` | `/login`, `/register`, `/logout` + timing-attack protection |
| `main_bp` | `routes/main.py` | `/`, `/chat` page routing |
| `chat_bp` | `routes/chat.py` | `/api/chats`, `/api/chats/<id>`, `/api/chats/bulk-delete`, `/api/messages` |
| `settings_bp` | `routes/settings.py` | `/settings` + `/api/settings` |
| `api_bp` | `routes/api.py` | `/api/models`, `/api/test-connection` (OLLAMA proxy) |

Rate limits are applied in `app.py` after blueprint registration (see `limiter.limit(...)` calls).

### Database models
- **User** — email + password_hash (Werkzeug), cascade to chats/settings
- **UserSettings** — per-user OLLAMA host
- **Chat** — conversation container with indexes `idx_chats_user_updated` and `idx_chats_user_created`
- **Message** — indexes `idx_messages_chat_created` and `idx_messages_chat_user`

Schema evolution uses **Flask-Migrate** (Alembic). See `migrations/versions/` for revision
scripts and `DEVELOPMENT.md` → "Database Migrations" for the workflow. `init_db()` runs
`flask db upgrade` on startup; legacy DBs without an `alembic_version` table are stamped
to HEAD automatically.

### OLLAMA integration
- Each user configures their own OLLAMA host (`UserSettings.ollama_host`)
- `OllamaClient` is instantiated per-request via `with OllamaClient(host) as client:` — no connection pool currently
- Supported operations: `get_models()`, `get_version()`, `chat()`, `generate()` (streaming also supported but not wired into routes yet)
- Extended timeout (120s) for slow model responses — blocks the worker for the duration
- Conversation context: last `CONVERSATION_HISTORY_LIMIT` messages (default 10)

### Frontend
- Jinja2 templates in `templates/`, base template inheritance
- Vanilla JS in `static/js/` — fetch API, CSRF via form tokens (not yet applied to JSON endpoints)
- Custom markdown renderer in `chat.js` (regex-based; `node_modules/` contains marked but it's not wired in)
- No WebSockets or SSE — manual polling / full-response waits

## Configuration Points

**Required env vars** (see `.env.example`):
- `SECRET_KEY` — cryptographic key (auto-generated in dev, required in prod)
- `FLASK_ENV` — `development` / `production` / `testing`
- `DATABASE_URL` — defaults to SQLite `instance/chat.db`
- `DEFAULT_OLLAMA_HOST` — default server URL (default `http://localhost:11434`)
- `RATELIMIT_STORAGE_URL` — rate limiter backend (default `memory://` — per-worker!)
- `LOG_LEVEL`, `LOG_TO_CONSOLE` — logging config

**Security posture:**
- CSRF enabled via Flask-WTF (form endpoints only — JSON API not yet protected)
- Session cookies: `HTTPONLY`, `SECURE` in production, `SAMESITE=Lax`
- CSP configured in `app.py` with `unsafe-inline` for script/style (to be tightened)
- HSTS emitted when `SESSION_COOKIE_SECURE` is true
- WTForms validation on form endpoints; `sanitize_message_content` + `html.escape` on chat messages

## Database Operations Pattern

```python
# Users
user = UserOperations.create_user(email, password)
user = UserOperations.authenticate_user(email, password)

# Chats
chat = ChatOperations.create_chat(user_id, title=None)
chats = ChatOperations.get_user_chats(user_id)
chats_with_counts = ChatOperations.get_user_chats_with_message_counts(user_id)

# Messages
message = MessageOperations.add_message(chat_id, content, is_user, model_name)
messages = MessageOperations.get_chat_messages(chat_id, user_id)
recent = MessageOperations.get_latest_messages(chat_id, limit=10)

# Settings
settings = SettingsOperations.get_user_settings(user_id)
SettingsOperations.update_ollama_host(user_id, new_host)
```

Always go through these classes — avoid raw SQLAlchemy in route handlers. Ownership checks (via `user_id`) are enforced inside the operations.

## Testing

**Unit tests** in `tests/test_*.py` — mock-based:
- `test_auth.py` — registration, login, logout
- `test_database.py` — CRUD on models
- `test_ollama.py` — `OllamaClient` with mocked HTTP
- `test_settings.py` — user settings CRUD

**Integration tests** in `tests/test_ollama_integration.py` — requires a live OLLAMA server, configurable endpoint.

No coverage tooling wired in yet — adding `pytest-cov` is tracked in `DEVELOPMENT_PLAN.md` (task 0.2).

## Common Development Patterns

### Adding a new route
1. Place handler in the appropriate blueprint file
2. Add `@login_required` for protected routes
3. Use the `*Operations` classes, not raw SQLAlchemy
4. Return JSON (`jsonify(...)`) for API, `render_template(...)` for pages
5. Register rate limit in `app.py` if the endpoint needs one

### Schema changes
1. Edit `models.py`
2. `FLASK_APP=app.py uv run flask db migrate -m "describe change"` — autogenerates a revision
3. Review the generated file in `migrations/versions/` (autogenerate is not perfect, especially for renames and SQLite ALTERs)
4. `FLASK_APP=app.py uv run flask db upgrade` to apply
5. Update `database_operations.py` if new fields need accessors

### OLLAMA client extensions
1. Add method to `OllamaClient` in `ollama_client.py`
2. Use `OllamaConnectionError` for network/API failures (maps to `ErrorHandler.external_service_error` in routes)
3. Keep per-request timeouts; don't set a global default
4. Add both unit test (mocked) and integration test

### Frontend JS
1. Use `fetch()` with CSRF token from the form (JSON endpoints are not yet CSRF-protected)
2. Update `formatMarkdown()` in `static/js/chat.js` for rendering changes
3. Keep XSS escaping in mind — the custom renderer is regex-based

## Files to Modify for Common Tasks

- **Auth**: `routes/auth.py`, `forms.py`, `models.py`
- **Schema**: `models.py`, `database_operations.py`, `migrations/versions/*`
- **OLLAMA**: `ollama_client.py`, `routes/api.py`, `routes/chat.py`
- **Frontend**: `templates/*.html`, `static/css/*.css`, `static/js/*.js`
- **Config**: `config.py`, `.env.example`
- **Error handling**: `error_handlers.py`
- **Rate limits**: `app.py` (applied post-registration), `rate_limiting.py` (defaults)
- **Logging**: `enhanced_logging.py`, `logs/`

## Production Considerations

- **SQLite** works for single-user / low-traffic only. For concurrency use PostgreSQL via `DATABASE_URL`.
- **Gunicorn** `--workers 4` — OLLAMA requests are I/O bound and block workers for up to 120s; consider gevent worker class for high concurrency.
- **Rate limiter** defaults to `memory://` — each worker has its own counters. Use Redis for shared limits.
- **HTTPS** required for `SESSION_COOKIE_SECURE`.
- **Logs** rotate in `logs/` (10MB app, 20MB access) — see `logs/README.md`.

## Known Limitations

- No streaming AI responses — full response blocks the worker and the UI
- Rate limiter uses in-memory backend by default (per-worker limits under gunicorn)
- JSON API endpoints are not CSRF-protected (form endpoints are)
- `UserSettings.ollama_host` accepts any URL — SSRF risk (no IP range / scheme whitelist)
- CSP allows `unsafe-inline` for script/style
- SQLite not suitable for high-concurrency production
- No user data export yet
- No chat search

All of the above are tracked in `DEVELOPMENT_PLAN.md`.

## Change History

Historical completion notes are consolidated in `CHANGELOG.md`.
