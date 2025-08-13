# Testovanie OLLAMA Chat aplikácie

Tento dokument popisuje ako spustiť a používať testy pre OLLAMA Chat aplikáciu.

## Štruktúra testov

```
tests/
├── __init__.py
├── test_auth.py          # Testy autentifikácie (login, register, logout)
├── test_database.py      # Testy databázových operácií (CRUD)
├── test_ollama.py        # Testy OLLAMA API klienta
└── test_settings.py      # Testy používateľských nastavení
```

## Inštalácia test závislostí

Testy používajú pytest framework, ktorý je už zahrnutý v pyproject.toml:

```bash
uv sync
```

## Spustenie testov

### Spustenie všetkých testov

```bash
uv run pytest tests/
```

**Poznámka:** Niektoré testy môžu zlyhávať po refactoringu na blueprints. Funkčné testy:
- `test_ollama.py` - všetky testy fungujú ✅
- `test_auth.py` - väčšina testov funguje ✅

### Spustenie konkrétneho test súboru

```bash
# Testy autentifikácie
uv run pytest tests/test_auth.py

# Testy databázy
uv run pytest tests/test_database.py

# Testy OLLAMA klienta
uv run pytest tests/test_ollama.py

# Testy nastavení
uv run pytest tests/test_settings.py
```

### Spustenie konkrétneho testu

```bash
# Spustenie konkrétnej test funkcie
uv run pytest tests/test_auth.py::test_user_login

# Spustenie testov s konkrétnym názvom
uv run pytest tests/ -k "login"
```

### Verbose výstup

```bash
# Detailný výstup
uv run pytest tests/ -v

# Ešte detailnejší výstup
uv run pytest tests/ -vv
```

### Coverage report

```bash
# Spustenie testov s coverage
uv run pytest tests/ --cov=. --cov-report=html

# Zobrazenie coverage v terminále
uv run pytest tests/ --cov=. --cov-report=term-missing
```

## Popis test súborov

### test_auth.py
Testuje autentifikačný systém:
- Načítanie login/register stránok
- Registráciu nových používateľov
- Prihlásenie existujúcich používateľov
- Validáciu neplatných údajov
- Logout funkcionalitu
- Presmerovanie neautentifikovaných používateľov

### test_database.py
Testuje databázové operácie:
- CRUD operácie pre všetky modely (User, Chat, Message, UserSettings)
- Vzťahy medzi modelmi
- Validáciu dát
- Izoláciu používateľských dát

### test_ollama.py
Testuje OLLAMA API klient:
- Pripojenie k serveru
- Načítanie modelov
- Chat komunikáciu
- Streaming responses
- Error handling
- Timeout handling

**Poznámka:** Tieto testy používajú mock objekty, takže nepotrebujú skutočný OLLAMA server.

### test_settings.py
Testuje používateľské nastavenia:
- Načítanie settings stránky
- Aktualizáciu OLLAMA host nastavení
- Validáciu URL formátov
- API endpoints pre testovanie pripojenia
- Načítanie modelov
- Izoláciu nastavení medzi používateľmi

## Test databáza

Všetky testy používajú dočasnú SQLite databázu, ktorá sa automaticky vytvorí a zmaže pre každý test. Testy neovplyvňujú produkčnú databázu.

## Mock objekty

Testy používajú mock objekty pre:
- HTTP požiadavky na OLLAMA server
- Databázové operácie (kde je to potrebné)
- External API calls

Toto umožňuje spustiť testy bez závislostí na externých službách.

## Continuous Integration

Pre CI/CD môžete použiť:

```bash
# Spustenie testov s exit code
uv run pytest tests/ --tb=short

# Spustenie s JUnit XML výstupom
uv run pytest tests/ --junitxml=test-results.xml
```

## Debugging testov

```bash
# Spustenie s pdb debuggerom
uv run pytest tests/ --pdb

# Zastavenie na prvej chybe
uv run pytest tests/ -x

# Zobrazenie print statements
uv run pytest tests/ -s
```

## Pridanie nových testov

Pri pridávaní nových testov:

1. Vytvorte nový súbor `test_*.py` v `tests/` adresári
2. Importujte potrebné moduly a fixtures
3. Použite `@pytest.fixture` pre setup/teardown
4. Pomenujte test funkcie `test_*`
5. Použite `assert` statements pre validáciu

Príklad:

```python
import pytest
from app import app
from models import db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

def test_my_feature(client):
    response = client.get('/my-endpoint')
    assert response.status_code == 200
```

## Troubleshooting

### Chyba "No module named 'app'"
Spustite testy z root adresára projektu:
```bash
cd /path/to/ollama-chat
uv run pytest tests/
```

### Databázové chyby
Uistite sa, že máte správne nastavené SQLALCHEMY_DATABASE_URI v test konfigurácii.

### Import chyby
Skontrolujte, že všetky závislosti sú nainštalované:
```bash
uv sync
```