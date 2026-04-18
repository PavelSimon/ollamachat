# Changelog

High-level history of improvements. Detailed historical notes are preserved in `docs/archive/`.
Forward-looking work is tracked in `DEVELOPMENT_PLAN.md`.

---

## 2026-04-18 — Test baseline & coverage tooling (plan task 0.2)

- Added `pytest-cov>=5.0.0` to dev dependencies; coverage config in `pyproject.toml` (source, omit patterns, exclude lines).
- Added `tests/conftest.py` with a shared `client` fixture that disposes the SQLAlchemy engine between tests — previously each test file had its own fixture and the engine was cached with a stale URI, causing cross-test DB pollution.
- Updated test credentials to comply with the current password policy (uppercase + special char) and switched hardcoded `192.168.1.23:11434` assertions to `localhost` or env-var-driven values so the suite is not tied to one developer's `.env`.
- Replaced `Mock()` with `MagicMock()` in `tests/test_settings.py` where the route uses `OllamaClient` as a context manager; `logged_in_user` fixture now returns a dict of primitive values to avoid `DetachedInstanceError`.
- Aligned expected status codes with the current `ErrorHandler` contract: `external_service_error` → 503, `internal_error` → 500.
- Added `Makefile` with `test`, `test-cov`, `dev`, `check-config` targets.

**Baseline coverage (2026-04-18):** 66% overall, 38 tests passing, 0 failing.
Per-module hot spots for future work:

| Module | Coverage | Notes |
|--------|---------:|-------|
| `routes/chat.py` | 14% | bulk-delete, send-message, chat CRUD untested |
| `routes/settings.py` | 43% | `validate_ollama_host` and `api_settings` PUT untested |
| `rate_limiting.py` | 46% | decorator wiring untested |
| `ollama_client.py` | 66% | streaming, version, error paths |
| `error_handlers.py` | 72% | `register_error_handlers` error-branch paths |

Integration tests (`tests/test_ollama_integration.py`) remain excluded from the default run (they require a live OLLAMA server) — they still run via `uv run python tests/test_ollama_integration.py`.

## 2026-04-18 — Documentation sync (plan task 0.1)

- Rewrote `CLAUDE.md` to match the actual codebase (removed false claims about `ollama_pool.py`, `response_cache.py`, and `routes/api_versions/` which were never implemented).
- Consolidated per-phase `*_COMPLETED.md` files into this changelog; originals moved to `docs/archive/`.
- Added `DEVELOPMENT_PLAN.md` with staged roadmap for security, stability, and performance work.

---

## Phase 3 — Observability & error handling (2025-08-16)

Source: `docs/archive/CODE_QUALITY_IMPROVEMENTS_COMPLETED.md`, `docs/archive/MAINTENANCE_IMPROVEMENTS_COMPLETED.md`.

**Added:**
- `enhanced_logging.py` — structured JSON logging with file rotation (10 MB app logs, 20 MB access logs), request correlation IDs, performance tracking. Logs land in `logs/` with `monitor.py` utility.
- `error_handlers.py` — centralized `ErrorHandler` and `StandardError` with error IDs, timestamps, standardized JSON responses, Marshmallow integration.
- `OllamaClient.get_version()` — OLLAMA server version display in the chat UI.
- `API_DOCUMENTATION.md` — endpoint reference with request/response schemas.
- Comprehensive docstrings across route handlers.

**Not delivered despite earlier documentation:**
- `ollama_pool.py` (connection pool) — never implemented; `OllamaClient` is still instantiated per-request.
- `response_cache.py` (TTL cache for model lists) — never implemented.
- `routes/api_versions/v1/*` (versioned API namespace) — never implemented; only `routes/api.py` exists.

These items are now back on the roadmap in `DEVELOPMENT_PLAN.md` (tasks 3.1, 3.2) as planned work rather than completed features.

---

## Phase 2 — Code quality & reliability (2025-08-16)

Source: `docs/archive/CODE_QUALITY_IMPROVEMENTS_COMPLETED.md`, `docs/archive/PERFORMANCE_IMPROVEMENTS_COMPLETED.md`.

**Error handling:**
- All routes migrated to `ErrorHandler` / `StandardError`; removed ad-hoc `jsonify({'error': ...})` patterns.
- Consistent Slovak user messages, English internal messages.
- Error IDs and timestamps on every error response.

**Database performance:**
- Fixed N+1 in chat listing — replaced `len(chat.messages)` with `get_user_chats_with_message_counts()` single query.
- SQLite pragmas (WAL, NORMAL sync, 64 MB cache, MEMORY temp store, foreign keys) applied via SQLAlchemy connect listener in `app.py`.
- Connection pool recycle set to 5 minutes, `pool_pre_ping` enabled.

**Memory management:**
- `OllamaClient` became a context manager; all routes use `with OllamaClient(host) as client:`.
- Explicit `response.close()` on HTTP responses.
- Reduced per-response memory footprint by extracting only essential fields.

**Config centralization:**
- Magic numbers moved to `config.py` (`MAX_MESSAGE_LENGTH`, `MAX_TITLE_LENGTH`, `CONVERSATION_HISTORY_LIMIT`, `AUTO_TITLE_*`, etc.).

---

## Phase 1 — Critical security & cleanup (2025-08-16)

Source: `docs/archive/PHASE1_SECURITY_CLEANUP_COMPLETED.md`, `docs/archive/SECURITY_ISSUES_PHASE2_COMPLETED.md`.

**Security headers (`app.py`):**
- Content-Security-Policy (still contains `unsafe-inline` — to be tightened, see `DEVELOPMENT_PLAN.md` §1.2)
- `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `X-XSS-Protection`, `Referrer-Policy`, `Permissions-Policy`
- HSTS when `SESSION_COOKIE_SECURE` is active

**Input validation:**
- Marshmallow schemas for API endpoints
- `sanitize_message_content` in `routes/chat.py` — strip, length limit, whitelist regex, `html.escape`
- WTForms validation on form endpoints

**Rate limiting (`app.py`, `rate_limiting.py`):**
- Flask-Limiter integrated with default limits "200/day, 50/hour"
- Per-endpoint limits: login 5/min, register 3/min, messages 20/min, bulk-delete 5/min, models 30/min
- Backend is memory by default (`RATELIMIT_STORAGE_URL=memory://`) — per-worker, see `DEVELOPMENT_PLAN.md` §2.2

**Auth hardening (`routes/auth.py`):**
- Timing-attack delay on login (minimum 0.1s regardless of outcome)
- Session fixation prevention
- Safe-redirect check on `next` parameter

**Cleanup:**
- Removed debug/test files from repo root (`debug_*.py`, `test_*` scripts, `simple_test_route.py`, `validation_schemas.py`)
- Debug mode restricted to `FLASK_ENV=development`

---

## Earlier history

See `docs/archive/WORK_SUMMARY_2025-08-13.md` for the pre-refactor snapshot and `git log` for fine-grained history.
