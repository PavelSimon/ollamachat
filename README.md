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
- `LOG_LEVEL` - Úroveň logovania (predvolene `ERROR` - len chyby)
- `VERBOSE_LOGS` - Nastavte na `true` pre podrobnejšie logovania (INFO level)
- `RATELIMIT_STORAGE_URL` - Úložisko pre rate limiting (predvolene `memory://`, v produkcii odporúčame Redis)

### Internet Search

Aplikácia podporuje internetové vyhľadávanie pre aktuálne informácie:

- **Toggle switch**: Zapnite/vypnite internetové vyhľadávanie vedľa tlačidla "Odoslať"
- **Zdroje**: DuckDuckGo Instant Answers + Wikipedia
- **Automatické**: AI model dostane aktuálne informácie z internetu ako kontext
- **Testovanie**: `python test_search.py` pre testovanie search funkcionality

### Logovania

Aplikácia má minimálne logovania (len chyby):

- **Predvolene**: Len ERROR level logy (chyby a pomalé požiadavky)
- **Podrobnejšie**: `VERBOSE_LOGS=true` pre INFO level logy
- **Konzola**: `LOG_TO_CONSOLE=true` pre zobrazenie logov v konzole
- **Súbory**: Logy sa ukladajú do `logs/` adresára

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

### Automatická konfigurácia
```bash
# Automatická konfigurácia development prostredia
uv run python setup-dev.py

# Spustenie development servera s auto-restart funkciou
uv run python dev.py

# Kontrola development prostredia
uv run python check-dev-env.py
```

### Manuálna konfigurácia
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

### Základné funkcie
- ✅ Používateľská autentifikácia s pokročilou bezpečnosťou (timing attack protection)
- ✅ Správa chatov (vytvorenie, mazanie, bulk delete, história)  
- ✅ Komunikácia s OLLAMA modelmi s kontextom posledných správ
- ✅ Konfigurovateľný OLLAMA server pre každého používateľa
- ✅ Responzívne webové rozhranie s markdown podporou
- ✅ Bezpečné ukladanie dát s optimalizovanými databázovými indexami

### Bezpečnosť a výkon
- ✅ Comprehensive input validation a sanitization (XSS ochrana)
- ✅ Rate limiting pre ochranu pred DoS útokmi (endpoint-specific)
- ✅ Session security s CSRF ochranou a secure cookies
- ✅ Centralizované error handling s štruktúrovanými JSON odpoveďami
- ✅ Memory leak prevention s proper resource cleanup
- ✅ SQLite performance optimizations (WAL mode, 64MB cache)
- ✅ Database query optimization (eliminované N+1 queries)

### Development & Monitoring
- ✅ Development server s auto-restart funkciou (`dev.py`)
- ✅ Automatická environment konfigurácia (`setup-dev.py`)
- ✅ Environment validation nástroje (`check-dev-env.py`)
- ✅ Comprehensive API dokumentácia
- ✅ Štruktúrované JSON logovania s automatickou rotáciou súborov
- ✅ Configuration constants pre všetky hardcoded hodnoty
- ✅ Organized test files v `tests/` directory

### API & Integration
- ✅ Real-time OLLAMA server version display
- ✅ Model selection s automatickým načítaním dostupných modelov
- ✅ Context-aware conversations (posledných 10 správ)
- ✅ Automatic chat title generation z prvej správy
- ✅ Bulk operations pre správu chatov
- ✅ Error handling s unique error IDs a timestamps