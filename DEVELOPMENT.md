# 🚀 OLLAMA Chat - Development Guide

This guide provides everything you need to set up and run the OLLAMA Chat application in development mode with auto-restart functionality.

## 📋 Quick Start

### 1. Prerequisites
- **Python 3.8+** (recommended: Python 3.13+)
- **uv** package manager ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- **OLLAMA server** running locally or remotely

### 2. One-Command Setup
```bash
# Run the automated setup
uv run python setup-dev.py
```

### 3. Start Development Server
```bash
# Start with auto-restart
uv run python dev.py
```

Visit: **http://127.0.0.1:5000**

---

## 🔧 Manual Setup (Alternative)

### Install Dependencies
```bash
# Install all dependencies including development tools
uv sync --dev

# Or install with specific groups
uv sync --extra production  # For production deployment
```

### Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# Required: Set SECRET_KEY for production
# Optional: Customize OLLAMA host, database, etc.
```

### Database Setup
```bash
# Initialize database (automatic in dev.py)
uv run python -c "from app import init_db; init_db()"
```

---

## 🛠️ Development Tools

### Development Server (`dev.py`)
**Features:**
- Auto-restart on file changes
- Enhanced logging to console
- Automatic database initialization
- File system monitoring
- Environment validation

**Usage:**
```bash
# Start development server
uv run python dev.py

# The server will:
# - Check dependencies
# - Setup environment
# - Initialize database
# - Start Flask with debug mode
# - Watch files for changes
# - Auto-restart on modifications
```

**File Patterns Watched:**
- Python files (`.py`)
- Templates (`.html`)
- Static assets (`.css`, `.js`)
- Configuration (`.json`, `.toml`)

**Directories Ignored:**
- `__pycache__`
- `.git`
- `node_modules`
- `instance`
- `logs`

### Environment Checker (`check-dev-env.py`)
Verifies your development environment:
```bash
uv run python check-dev-env.py
```

**Checks:**
- Required files exist
- Dependencies installed
- Environment variables
- External tools (uv, python)
- Directory structure

### Setup Script (`setup-dev.py`)
Automated development environment setup:
```bash
uv run python setup-dev.py
```

**Features:**
- Dependency installation
- Environment file creation
- Directory structure setup
- Import validation
- Secure secret key generation

---

## 📁 Project Structure

```
ollama-chat/
├── 🚀 Development Tools
│   ├── dev.py              # Development server with auto-restart
│   ├── setup-dev.py        # Automated setup script
│   ├── check-dev-env.py    # Environment verification
│   └── .env.example        # Environment template
│
├── 🔧 Core Application
│   ├── app.py              # Flask application factory
│   ├── config.py           # Configuration classes
│   ├── models.py           # Database models
│   ├── forms.py            # WTForms definitions
│   └── database_operations.py  # Database abstractions
│
├── 🛣️ Routes & APIs
│   ├── routes/auth.py      # Authentication (login/register)
│   ├── routes/main.py      # Main pages (index, chat)
│   ├── routes/chat.py      # Chat API (CRUD, messaging)
│   ├── routes/api.py       # OLLAMA API (models, connection)
│   └── routes/settings.py  # User settings
│
├── 🎨 Frontend
│   ├── templates/          # Jinja2 HTML templates
│   ├── static/css/         # Stylesheets
│   └── static/js/          # JavaScript files
│
├── 🧪 Testing
│   ├── tests/              # Test files
│   └── pyproject.toml      # Test configuration
│
├── 📊 Data & Logs
│   ├── instance/           # SQLite database
│   └── logs/               # Application logs
│
└── 📚 Documentation
    ├── CLAUDE.md           # Project instructions
    ├── DEVELOPMENT.md      # This file
    ├── README.md           # Project overview
    └── DEPLOYMENT.md       # Production deployment
```

---

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=1

# Security (REQUIRED for production)
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=sqlite:///chat.db

# OLLAMA Server
DEFAULT_OLLAMA_HOST=http://localhost:11434

# Logging
LOG_LEVEL=INFO
LOG_TO_CONSOLE=true

# Rate Limiting
RATELIMIT_STORAGE_URL=memory://
```

### Development vs Production
| Setting | Development | Production |
|---------|-------------|------------|
| FLASK_ENV | development | production |
| FLASK_DEBUG | 1 | 0 |
| SECRET_KEY | auto-generated | required |
| DATABASE_URL | SQLite | PostgreSQL/MySQL |
| LOG_TO_CONSOLE | true | false |
| SESSION_COOKIE_SECURE | false | true |

---

## 🧪 Testing

### Run Tests
```bash
# All tests
uv run pytest

# Specific test file
uv run pytest tests/test_auth.py

# With coverage
uv run pytest --cov=.

# Integration tests (requires OLLAMA server)
uv run python tests/test_ollama_integration.py
```

### Test Categories
- **Unit Tests**: Mock-based testing in `tests/`
- **Integration Tests**: Real OLLAMA server testing
- **Authentication Tests**: Login/register flows
- **Database Tests**: Model operations
- **Settings Tests**: Configuration management

---

## 🔍 Debugging & Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Find process using port 5000
netstat -ano | findstr :5000    # Windows
lsof -i :5000                   # macOS/Linux

# Kill process or use different port in dev.py
```

#### 2. Missing Dependencies
```bash
# Reinstall dependencies
uv sync --dev

# Check specific module
uv run python -c "import flask"
```

#### 3. Database Issues
```bash
# Reset database
rm instance/chat.db
uv run python -c "from app import init_db; init_db()"
```

#### 4. OLLAMA Connection Issues
```bash
# Test OLLAMA server
curl http://localhost:11434/api/version

# Check settings in browser
http://127.0.0.1:5000/settings
```

### Debug Mode Features
- **Debug Toolbar**: Flask debug information
- **Auto-reload**: Automatic server restart
- **Error Pages**: Detailed error information
- **Console Logging**: All logs to terminal
- **SQL Logging**: Database query logging

### Logging
```bash
# View logs in real-time
tail -f logs/ollama_chat.log     # Application logs
tail -f logs/access.log          # HTTP requests
tail -f logs/errors.log          # Error logs
```

---

## 📚 Development Workflow

### 1. Starting Development
```bash
# Check environment
uv run python check-dev-env.py

# Start development server
uv run python dev.py

# Open browser
open http://127.0.0.1:5000
```

### 2. Making Changes
- Edit files in your preferred editor
- Server automatically restarts on changes
- Refresh browser to see updates
- Check console for any errors

### 3. Adding Features
1. **Backend**: Add routes in `routes/`
2. **Frontend**: Add templates/static files
3. **Database**: Modify `models.py`
4. **Tests**: Add tests in `tests/`
5. **Documentation**: Update relevant docs

### 4. Before Committing
```bash
# Run tests
uv run pytest

# Check code style (if configured)
uv run python -m flake8

# Verify app starts
uv run python check-dev-env.py
```

---

## 🔧 Advanced Configuration

### Custom OLLAMA Server
```bash
# In .env file
DEFAULT_OLLAMA_HOST=http://192.168.1.100:11434

# Or set environment variable
export DEFAULT_OLLAMA_HOST=http://192.168.1.100:11434
```

### Database Alternatives
```bash
# PostgreSQL
DATABASE_URL=postgresql://user:password@localhost/ollama_chat

# MySQL
DATABASE_URL=mysql://user:password@localhost/ollama_chat
```

### Custom Development Settings
Edit `dev.py` to customize:
- **Port**: Change Flask port (default: 5000)
- **Host**: Change bind address (default: 127.0.0.1)
- **Watch patterns**: Add/remove file types to watch
- **Restart delay**: Modify restart timing

---

## 🚀 Performance Tips

### Development
- Use SSD for faster file watching
- Exclude large directories from file watcher
- Use virtual environment for isolation
- Enable SQLite WAL mode for better concurrency

### Debugging
- Use browser dev tools for frontend debugging
- Use Flask debug toolbar for backend analysis
- Monitor logs for performance issues
- Profile slow database queries

---

## 🆘 Help & Support

### Documentation
- **Project Guide**: `CLAUDE.md`
- **Deployment**: `DEPLOYMENT.md`
- **API Documentation**: (auto-generated in development)

### Troubleshooting Tools
```bash
# Environment check
uv run python check-dev-env.py

# Configuration validation
uv run python validate_config.py

# Database migration (if needed)
uv run python migrate_database.py
```

### Database Migrations

The project uses **Flask-Migrate** (Alembic) for schema evolution. Migrations live in `migrations/versions/`.

**Typical workflow when editing `models.py`:**
```bash
# 1. Edit models.py to add/change columns or tables
# 2. Autogenerate a migration from the diff between models and the live DB
FLASK_APP=app.py uv run flask db migrate -m "describe the change"
# 3. Review the generated file in migrations/versions/ — autogenerate is not perfect
# 4. Apply the migration
FLASK_APP=app.py uv run flask db upgrade
```

**Fresh environment:**
```bash
FLASK_APP=app.py uv run flask db upgrade     # builds the schema from scratch
```

**Existing production DB that predates Flask-Migrate** (was created by `db.create_all()`
and has no `alembic_version` table):
```bash
FLASK_APP=app.py uv run flask db stamp head  # tell Alembic the DB is already at HEAD
FLASK_APP=app.py uv run flask db upgrade     # future migrations can now apply
```

`init_db()` in `app.py` handles the common cases automatically: it runs `upgrade()` on
a fresh DB and stamps legacy DBs before upgrading. For most dev work, `init_db()` is
enough; the CLI is there for more control when you need it.

**Rolling back:**
```bash
FLASK_APP=app.py uv run flask db downgrade -1   # one revision back
FLASK_APP=app.py uv run flask db downgrade base # to empty schema
```

The legacy `migrate_database.py` script that added performance indexes is still in the
repo as historical reference, but the equivalent (and all future) index work should go
through Flask-Migrate.

### Common Commands Reference
```bash
# Setup
uv run python setup-dev.py           # Full setup
cp .env.example .env                  # Environment setup

# Development
uv run python dev.py                 # Start dev server
uv run python check-dev-env.py       # Check environment
uv run python app.py                 # Start production-like server

# Dependencies
uv sync --dev                        # Install dev dependencies
uv add package-name                  # Add new dependency
uv remove package-name               # Remove dependency

# Testing
uv run pytest                        # Run all tests
uv run pytest tests/test_auth.py     # Run specific tests
uv run python tests/test_ollama_integration.py  # Integration tests

# Database migrations (Flask-Migrate / Alembic)
FLASK_APP=app.py uv run flask db upgrade        # apply all pending migrations
FLASK_APP=app.py uv run flask db migrate -m "msg"  # autogenerate migration from models.py
FLASK_APP=app.py uv run flask db current        # show current revision
FLASK_APP=app.py uv run flask db history        # list all revisions
FLASK_APP=app.py uv run flask db stamp head     # mark legacy DB as up-to-date
uv run python -c "from app import init_db; init_db()"  # upgrade or stamp as needed

# Validation
uv run python validate_config.py     # Check configuration
```

---

## ✅ Quick Checklist

### First Time Setup
- [ ] Python 3.8+ installed
- [ ] uv package manager installed
- [ ] OLLAMA server running
- [ ] Run `uv run python setup-dev.py`
- [ ] Start dev server: `uv run python dev.py`
- [ ] Visit http://127.0.0.1:5000

### Daily Development
- [ ] Pull latest changes
- [ ] Run `uv sync --dev` if dependencies changed
- [ ] Start `uv run python dev.py`
- [ ] Make changes, server auto-restarts
- [ ] Run tests before committing
- [ ] Check logs for any issues

### Before Deployment
- [ ] All tests pass
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Static files collected
- [ ] Security settings reviewed

---

**Happy Development! 🚀**

For questions or issues, check the project documentation or create an issue in the repository.