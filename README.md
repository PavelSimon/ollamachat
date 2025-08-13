# OLLAMA Chat

Jednoduchá webová aplikácia pre komunikáciu s lokálnym OLLAMA modelom.
Vytvorené pomocou [kiro.dev](https://kiro.dev)

## Požiadavky

- Python 3.8+
- uv (Python package manager)
- OLLAMA server

## Inštalácia

1. Nainštalujte uv ak ho nemáte:
```bash
# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Klonujte projekt a nainštalujte závislosti:
```bash
git clone <repository-url>
cd ollama-chat
uv sync
```

3. Nakonfigurujte prostredie:
```bash
# Skopírujte príklad konfigurácie
cp .env.example .env

# Editujte .env súbor a nastavte potrebné premenné
# DÔLEŽITÉ: V produkcii vygenerujte bezpečný SECRET_KEY:
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
```

## Spustenie

```bash
# Inštalácia závislostí a spustenie
uv sync
uv run app.py
```

Alebo môžete použiť tradičný prístup:
```bash
# Vytvorenie virtuálneho prostredia
uv venv
# Aktivácia (Windows)
.venv\Scripts\activate
# Aktivácia (macOS/Linux)  
source .venv/bin/activate
# Inštalácia závislostí
uv pip install -e .
# Spustenie
python app.py
```

Aplikácia bude dostupná na `http://localhost:5000`

## Konfigurácia

### Premenné prostredia

Aplikácia používa nasledujúce premenné prostredia (definované v `.env` súbore):

- `SECRET_KEY` - **POVINNÝ v produkcii!** Kryptografický kľúč pre session a CSRF ochranu
- `FLASK_ENV` - Prostredie aplikácie (`development`, `production`, `testing`)
- `DATABASE_URL` - Pripojovací reťazec k databáze (predvolene SQLite)
- `DEFAULT_OLLAMA_HOST` - Predvolený OLLAMA server (predvolene `http://localhost:11434`)
- `LOG_LEVEL` - Úroveň logovania (predvolene `INFO`)
- `RATELIMIT_STORAGE_URL` - Úložisko pre rate limiting (predvolene `memory://`, v produkcii odporúčame Redis)

### Bezpečnostné upozornenia

⚠️ **DÔLEŽITÉ pre produkčné nasadenie:**

1. **Vždy nastavte vlastný SECRET_KEY:**
   ```bash
   # Vygenerujte bezpečný kľúč
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **Použite HTTPS v produkcii** - nastavte `SESSION_COOKIE_SECURE=true` v `.env`

3. **Použite robustnú databázu** - SQLite nie je vhodný pre produkciu s viacerými používateľmi

### Základné nastavenia

- Predvolený OLLAMA server: `http://localhost:11434` (konfigurovateľný)
- Databáza: SQLite v `instance/chat.db` (konfigurovateľná)
- Nastavenia možno zmeniť v aplikácii po prihlásení alebo v `.env` súbore

## Vývoj

```bash
# Inštalácia dev závislostí
uv sync --dev

# Spustenie testov
uv run pytest

# Testovanie OLLAMA pripojenia (integration test)
uv run python tests/test_ollama_integration.py

# Testovanie s vlastným OLLAMA serverom
uv run python tests/test_ollama_integration.py http://your-server:11434

# Validácia konfigurácie
uv run python validate_config.py

# Migrácia databázy (pridanie výkonnostných indexov)
uv run python migrate_database.py
```

### Typy testov

- **Unit testy** (`tests/test_ollama.py`): Testujú funkcionalitu s mock objektmi
- **Integration testy** (`tests/test_ollama_integration.py`): Testujú skutočné pripojenie k OLLAMA serveru

Detailnú dokumentáciu testov nájdete v [tests.md](tests.md).

## Production Deployment

Pre produkčné nasadenie si prečítajte [DEPLOYMENT.md](DEPLOYMENT.md).

### Rýchle Docker spustenie

```bash
# Vytvorte .env súbor
cp .env.example .env

# Spustite s Docker Compose
docker-compose up -d
```

## Funkcie

- ✅ Používateľská autentifikácia (registrácia/prihlásenie)
- ✅ Správa chatov (vytvorenie, mazanie, história)
- ✅ Komunikácia s OLLAMA modelmi
- ✅ Konfigurovateľný OLLAMA server
- ✅ Responzívne webové rozhranie
- ✅ Bezpečné ukladanie dát (SQLite)
- ✅ Real-time chat rozhranie
- ✅ Model selection (výber AI modelu)
- ✅ Organizovaný CSS a JavaScript (static/css/, static/js/)
- ✅ Rozšírené timeout handling pre pomalé modely
- ✅ Diagnostické nástroje a integration testy
- ✅ Comprehensive input validation pre všetky API endpointy
- ✅ Databázové indexy pre optimalizovaný výkon
- ✅ Rate limiting pre ochranu pred DoS útokmi