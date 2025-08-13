# Design Document

## Overview

OLLAMA Chat je jednoduchá webová aplikácia postavená na Python Flask frameworku s SQLite databázou. Aplikácia poskytuje chat rozhranie pre komunikáciu s lokálnymi OLLAMA AI modelmi s podporou viacerých používateľov, správy chatov a konfigurácie servera.

## Architecture

### Technology Stack
- **Backend Framework**: Flask (Python) - najjednoduchší framework na vývoj aj beh
- **Database**: SQLite - ľahká, súborová databáza bez potreby servera
- **Frontend**: HTML templates s Jinja2, minimálne CSS, vanilla JavaScript
- **Authentication**: Flask-Login pre session management
- **HTTP Client**: requests library pre komunikáciu s OLLAMA API

### System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │◄──►│   Flask App     │◄──►│   SQLite DB     │
│                 │    │                 │    │                 │
│ - HTML/CSS/JS   │    │ - Routes        │    │ - Users         │
│ - Chat UI       │    │ - Auth          │    │ - Chats         │
│ - Settings      │    │ - API calls     │    │ - Messages      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  OLLAMA Server  │
                       │                 │
                       │ - Models API    │
                       │ - Chat API      │
                       └─────────────────┘
```

## Components and Interfaces

### 1. Authentication System
- **User Registration/Login**: Flask-WTF forms pre bezpečné spracovanie
- **Session Management**: Flask-Login pre správu prihlásených používateľov
- **Password Security**: Werkzeug pre hashovanie hesiel

### 2. Database Layer
**Tables:**
```sql
users (
    id INTEGER PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

chats (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    title TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

messages (
    id INTEGER PRIMARY KEY,
    chat_id INTEGER REFERENCES chats(id),
    content TEXT NOT NULL,
    is_user BOOLEAN NOT NULL,
    model_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

user_settings (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    ollama_host TEXT DEFAULT 'http://192.168.1.23:11434',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### 3. OLLAMA Integration
**OllamaClient Class:**
```python
class OllamaClient:
    def __init__(self, base_url):
        self.base_url = base_url
    
    def get_models(self):
        # GET /api/tags
    
    def chat(self, model, messages):
        # POST /api/chat
    
    def test_connection(self):
        # Test server availability
```

### 4. Web Routes Structure
```
/ (GET) - Redirect to login or chat
/login (GET, POST) - Login form
/register (GET, POST) - Registration form
/logout (POST) - Logout user
/chat (GET) - Main chat interface
/api/chats (GET, POST) - Chat management
/api/chats/<id> (GET, DELETE) - Specific chat operations
/api/messages (POST) - Send message to AI
/api/models (GET) - Get available models
/settings (GET, POST) - User settings
```

## Data Models

### User Model
```python
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    chats = db.relationship('Chat', backref='user', lazy=True)
    settings = db.relationship('UserSettings', backref='user', uselist=False)
```

### Chat Model
```python
class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship('Message', backref='chat', lazy=True)
```

### Message Model
```python
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_user = db.Column(db.Boolean, nullable=False)
    model_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

## Error Handling

### OLLAMA Connection Errors
- **Connection Timeout**: Zobrazenie chybovej správy s možnosťou zmeny nastavení
- **Invalid Response**: Loggovanie chyby a user-friendly správa
- **Model Not Available**: Automatické prepnutie na dostupný model

### Database Errors
- **Connection Issues**: Graceful degradation s chybovou správou
- **Constraint Violations**: Validácia na aplikačnej úrovni
- **Migration Errors**: Automatické vytvorenie tabuliek pri prvom spustení

### Authentication Errors
- **Invalid Credentials**: Bezpečné chybové správy bez úniku informácií
- **Session Expiry**: Automatické presmerovanie na login
- **CSRF Protection**: Flask-WTF tokeny pre všetky formuláre

## Testing Strategy

### Unit Tests
- **Models**: Testovanie databázových operácií
- **OllamaClient**: Mock testovanie API calls
- **Authentication**: Testovanie login/logout flow

### Integration Tests
- **API Endpoints**: Testovanie všetkých routes
- **Database Operations**: End-to-end testovanie s test databázou
- **OLLAMA Integration**: Testovanie s mock OLLAMA serverom

### Frontend Testing
- **Form Validation**: JavaScript validácia formulárov
- **Chat Interface**: Testovanie posielania správ
- **Responsive Design**: Testovanie na rôznych zariadeniach

## Security Considerations

### Authentication Security
- **Password Hashing**: Werkzeug PBKDF2 hashing
- **Session Security**: Secure cookies, CSRF protection
- **Input Validation**: WTForms validácia všetkých vstupov

### Data Protection
- **User Isolation**: Každý používateľ vidí iba svoje dáta
- **SQL Injection Prevention**: SQLAlchemy ORM
- **XSS Protection**: Jinja2 auto-escaping

## Performance Considerations

### Database Optimization
- **Indexy**: Na user_id, chat_id pre rýchle queries
- **Connection Pooling**: SQLite connection reuse
- **Query Optimization**: Eager loading pre related data

### Frontend Performance
- **Minimal JavaScript**: Vanilla JS bez heavy frameworks
- **CSS Optimization**: Inline critical CSS
- **Asset Compression**: Gzip compression pre statické súbory

## Deployment Architecture

### Development Setup
```
ollama-chat/
├── app.py              # Main Flask application
├── models.py           # Database models
├── ollama_client.py    # OLLAMA API client
├── forms.py            # WTForms definitions
├── templates/          # Jinja2 templates
│   ├── base.html
│   ├── login.html
│   ├── chat.html
│   └── settings.html
├── static/             # CSS, JS, images
│   ├── style.css
│   └── app.js
├── pyproject.toml      # Python dependencies (uv)
├── README.md           # Setup instructions
└── instance/           # SQLite database location
    └── chat.db
```

### Production Considerations
- **WSGI Server**: Gunicorn pre production deployment
- **Reverse Proxy**: Nginx pre statické súbory
- **Database Backup**: Pravidelné zálohy SQLite súboru
- **Environment Variables**: Konfigurácia cez .env súbor