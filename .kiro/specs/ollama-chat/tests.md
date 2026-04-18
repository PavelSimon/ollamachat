# Testovanie OLLAMA Chat aplikácie

Tento dokument popisuje ako spustiť a používať testy pre OLLAMA Chat aplikáciu.

## Štruktúra testov

```
tests/
├── __init__.py
├── test_auth.py                 # Testy autentifikácie (login, register, logout)
├── test_database.py             # Testy databázových operácií (CRUD)
├── test_ollama.py               # Unit testy OLLAMA API klienta (s mock objektmi)
├── test_ollama_integration.py   # Integration testy OLLAMA servera (skutočné pripojenie)
└── test_settings.py             # Testy používateľských nastavení
```

## Inštalácia test závislostí

Testy používajú pytest framework, ktorý je už zahrnutý v pyproject.toml:

```bash
uv sync
```

## Spustenie testov

### Spustenie všetkých unit testov

```bash
uv run pytest tests/
```

**Poznámka:** Niektoré testy môžu zlyhávať po refactoringu na blueprints. Funkčné testy:
- `test_ollama.py` - všetky testy fungujú ✅
- `test_auth.py` - väčšina testov funguje ✅

### Spustenie integration testov

```bash
# Testovanie skutočného OLLAMA servera (predvolený host)
uv run python tests/test_ollama_integration.py

# Testovanie s vlastným OLLAMA serverom
uv run python tests/test_ollama_integration.py http://your-server:11434
```

### Spustenie konkrétneho test súboru

```bash
# Testy autentifikácie
uv run pytest tests/test_auth.py

# Testy databázy
uv run pytest tests/test_database.py

# Unit testy OLLAMA klienta (s mock objektmi)
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

### test_ollama.py (Unit testy)
Testuje OLLAMA API klient s mock objektmi:
- Pripojenie k serveru
- Načítanie modelov
- Chat komunikáciu
- Streaming responses
- Error handling
- Timeout handling

**Poznámka:** Tieto testy používajú mock objekty, takže nepotrebujú skutočný OLLAMA server.

### test_ollama_integration.py (Integration testy)
Testuje skutočné pripojenie k OLLAMA serveru:
- Testovanie pripojenia k serveru
- Načítanie dostupných modelov
- Skutočnú chat komunikáciu s AI modelom
- Meranie výkonu a response time
- Diagnostiku problémov s pripojením

**Poznámka:** Tieto testy vyžadujú bežiaci OLLAMA server s nainštalovanými modelmi.

### test_settings.py
Testuje používateľské nastavenia:
- Načítanie settings stránky
- Aktualizáciu OLLAMA host nastavení
- Validáciu URL formátov
- API endpoints pre testovanie pripojenia
- Načítanie modelov
- Izoláciu nastavení medzi používateľmi

## Typy testov

### Unit testy
- **Účel**: Rýchle testovanie jednotlivých komponentov
- **Výhody**: Rýchle, nezávislé na externých službách
- **Spustenie**: `uv run pytest tests/`
- **Použitie**: Vývoj, CI/CD pipeline

### Integration testy
- **Účel**: Testovanie skutočného pripojenia k OLLAMA serveru
- **Výhody**: Overenie funkčnosti v reálnom prostredí
- **Spustenie**: `uv run python tests/test_ollama_integration.py`
- **Použitie**: Diagnostika, troubleshooting, deployment testing

## Test databáza

Všetky testy používajú dočasnú SQLite databázu, ktorá sa automaticky vytvorí a zmaže pre každý test. Testy neovplyvňujú produkčnú databázu.

## Mock objekty

Unit testy používajú mock objekty pre:
- HTTP požiadavky na OLLAMA server
- Databázové operácie (kde je to potrebné)
- External API calls

Toto umožňuje spustiť testy bez závislostí na externých službách.

## Continuous Integration

Pre CI/CD môžete použiť:

```bash
# Spustenie unit testov s exit code
uv run pytest tests/ --tb=short

# Spustenie s JUnit XML výstupom
uv run pytest tests/ --junitxml=test-results.xml

# Integration testy v CI (ak je OLLAMA server dostupný)
uv run python tests/test_ollama_integration.py $OLLAMA_HOST
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

## Diagnostika OLLAMA problémov

Pre diagnostiku problémov s OLLAMA serverom použite integration test:

```bash
# Základné testovanie
uv run python tests/test_ollama_integration.py

# Testovanie s vlastným serverom
uv run python tests/test_ollama_integration.py http://192.168.1.100:11434

# Verbose výstup pre diagnostiku
uv run python tests/test_ollama_integration.py http://localhost:11434
```

Integration test vám ukáže:
- ✅/❌ Stav pripojenia k serveru
- 📋 Zoznam dostupných modelov a ich veľkosti
- ⏱️ Response time pre chat požiadavky
- 📊 Štatistiky výkonu (tokens, duration)

## Pridanie nových testov

Pri pridávaní nových testov:

1. **Unit testy**: Vytvorte nový súbor `test_*.py` v `tests/` adresári
2. **Integration testy**: Rozšírte `test_ollama_integration.py`
3. Importujte potrebné moduly a fixtures
4. Použite `@pytest.fixture` pre setup/teardown
5. Pomenujte test funkcie `test_*`
6. Použite `assert` statements pre validáciu

Príklad unit testu:

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

Príklad integration testu:

```python
def test_new_ollama_feature():
    """Test new OLLAMA server feature"""
    client = OllamaClient("http://localhost:11434")
    
    try:
        result = client.new_feature()
        print(f"✓ New feature works: {result}")
        return True
    except Exception as e:
        print(f"✗ New feature failed: {e}")
        return False
```

## Troubleshooting

### Chyba "No module named 'app'"
Spustite testy z root adresára projektu:
```bash
cd /path/to/ollama-chat
uv run pytest tests/
```

### Integration test zlyháva
1. Skontrolujte, že OLLAMA server beží:
   ```bash
   curl http://localhost:11434/api/tags
   ```
2. Overte, že máte nainštalované modely:
   ```bash
   ollama list
   ```
3. Skúste iný host/port:
   ```bash
   uv run python tests/test_ollama_integration.py http://your-host:11434
   ```

### Databázové chyby
Uistite sa, že máte správne nastavené SQLALCHEMY_DATABASE_URI v test konfigurácii.

### Import chyby
Skontrolujte, že všetky závislosti sú nainštalované:
```bash
uv sync
```

### Timeout chyby v integration testoch
- Skontrolujte výkon OLLAMA servera
- Skúste menší model pre testovanie
- Zvýšte timeout v `test_ollama_integration.py`

## Odporúčané workflow

1. **Počas vývoja**: Spúšťajte unit testy (`pytest tests/`)
2. **Pred commitom**: Spustite všetky unit testy
3. **Pred deploymentom**: Spustite integration testy
4. **Pri problémoch**: Použite integration test pre diagnostiku
5. **V CI/CD**: Unit testy vždy, integration testy ak je server dostupný