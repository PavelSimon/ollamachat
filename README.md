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

- Predvolený OLLAMA server: `http://192.168.1.23:11434`
- Databáza: SQLite v `instance/chat.db`
- Nastavenia možno zmeniť v aplikácii po prihlásení

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
```

### Typy testov

- **Unit testy** (`tests/test_ollama.py`): Testujú funkcionalitu s mock objektmi
- **Integration testy** (`tests/test_ollama_integration.py`): Testujú skutočné pripojenie k OLLAMA serveru

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
- ✅ Minimálny CSS a JavaScript