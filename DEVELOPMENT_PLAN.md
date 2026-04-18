# Plán postupného vývoja — OLLAMA Chat

Plán vychádza z analýzy stavu kódbase k **2026-04-18**. Rieši tri oblasti: **bezpečnosť**, **stabilita**, **výkon**. Úlohy sú zoradené podľa rizika a závislostí — neskoršie fázy stavajú na predchádzajúcich.

Každá úloha má:
- **Cieľ** — čo sa rieši a prečo
- **Zmeny** — ktoré súbory sa upravia
- **Akceptačné kritériá** — ako overíme, že je hotovo
- **Odhad** — rádovo človekohodiny (h) alebo dni (d)
- **Závislosť** — predchádzajúce úlohy, ktoré musia byť hotové

Legenda priority: 🔴 kritická · 🟠 vysoká · 🟡 stredná · 🟢 nízka

---

## Fáza 0 — Hygiena a príprava (1–2 dni)

Cieľom je dostať repo do stavu, kde ďalšie zmeny vieme bezpečne overovať.

### 0.1 🔴 Synchronizácia CLAUDE.md s realitou
- **Cieľ**: CLAUDE.md tvrdí existenciu `ollama_pool.py`, `response_cache.py`, `routes/api_versions/v1/*` — tieto súbory v repo nie sú. Odstrániť falošné nároky, aby budúca práca nestála na mýtoch.
- **Zmeny**: `CLAUDE.md`, konsolidácia `*_COMPLETED.md` súborov do jedného `CHANGELOG.md`.
- **Akceptácia**: každý odkaz v CLAUDE.md zodpovedá reálnemu súboru/funkcii; `grep` na spomínané moduly vracia výsledky.
- **Odhad**: 2 h

### 0.2 🟠 Rozšírenie test coverage baseline
- **Cieľ**: Pred veľkými zmenami vedieť, čo prestane fungovať. Aktuálne je 5 test súborov, coverage neznámy.
- **Zmeny**: pridať `pytest-cov`, `pyproject.toml` config, CI workflow (alebo aspoň `make test`).
- **Akceptácia**: `uv run pytest --cov` beží, coverage report generovaný, baseline zaznamenaný v `CHANGELOG.md`.
- **Odhad**: 4 h

### 0.3 🟡 Flask-Migrate (Alembic)
- **Cieľ**: Bez migrácií sa `models.py` nedá meniť v produkcii bez straty dát. Všetky ďalšie fázy menia schému.
- **Zmeny**: `pyproject.toml` (+`Flask-Migrate`), `app.py` (init), `migrations/` adresár, prvá migrácia = snapshot aktuálneho stavu.
- **Akceptácia**: `flask db upgrade` na čerstvej DB vytvorí identickú schému ako `db.create_all()`; `DEVELOPMENT.md` má sekciu "Migrations".
- **Odhad**: 4 h
- **Závisí od**: 0.2

---

## Fáza 1 — Kritická bezpečnosť (3–5 dní)

### 1.1 🔴 SSRF ochrana pre OLLAMA host
- **Cieľ**: Používateľ si môže v settings nastaviť `http://169.254.169.254/` alebo `http://127.0.0.1:22` a aplikácia z neho robí requesty zo servera. Teraz = plný SSRF.
- **Zmeny**:
  - Nový `security/url_validator.py` s funkciou `validate_ollama_host(url) -> str`
  - Validácia: len `http`/`https`, blokovať RFC1918, loopback, link-local, multicast, reserved; DNS resolve → opäť check IP (ochrana pred `evil.com → 127.0.0.1`); povoliť port iba z whitelistu (default 11434, config-overridable pre lokálne dev).
  - Integrácia v `forms.py` (SettingsForm), `routes/settings.py`, `routes/api.py` test-connection.
  - Tests: `tests/test_url_validator.py` s negatívnymi prípadmi (metadata IP, DNS rebind, redirect).
- **Akceptácia**: manuálne pokusy nastaviť `http://127.0.0.1:11434`, `http://169.254.169.254/`, `file:///etc/passwd` sa odmietnu s 400.
- **Odhad**: 1 d
- **Závisí od**: 0.2

### 1.2 🔴 CSP bez `unsafe-inline`
- **Cieľ**: Aktuálna CSP `script-src 'self' 'unsafe-inline'` prakticky vypína ochranu proti XSS. Pri zlyhaní sanitizácie je XSS triviálna.
- **Zmeny**:
  - Audit `templates/*.html` — nájsť všetky `<script>...</script>` a `on*=""` handlery, presunúť do `static/js/`.
  - Inline `style=""` → CSS triedy v `static/css/`.
  - `app.py:147` — CSP bez `unsafe-inline`, prípadne nonce generovaný v `before_request` a injectnutý cez Jinja context processor.
- **Akceptácia**: v DevTools žiadne CSP violations pri login/register/chat/settings flows; `curl -I` header neobsahuje `unsafe-inline`.
- **Odhad**: 1 d

### 1.3 🔴 CSRF pre JSON API endpointy
- **Cieľ**: Flask-WTF CSRF sa nevzťahuje na `application/json` POST endpointy. Útočník môže zo škodlivej stránky spraviť `fetch('/api/messages', {method:'POST', credentials:'include', ...})`.
- **Zmeny**:
  - `app.py` — `before_request` hook overujúci `X-CSRF-Token` header proti session tokenu pre všetky `POST|PUT|DELETE` na `/api/*`.
  - `static/js/chat.js`, `settings.js` — čítať token z `<meta name="csrf-token">` a posielať v každom fetch.
  - `templates/base.html` — meta tag s tokenom.
  - Alternatíva: `SESSION_COOKIE_SAMESITE='Strict'` + Origin header check (jednoduchšie, slabšie pri subdoménach).
- **Akceptácia**: integračný test `test_csrf.py` potvrdí 403 bez tokenu a 200 s tokenom; manuálne cross-origin curl bez tokenu → 403.
- **Odhad**: 1 d

### 1.4 🟠 Odstránenie whitelist regex v `sanitize_message_content`
- **Cieľ**: Regex v `routes/chat.py:46` zahadzuje emoji, CJK znaky, matematické symboly — funkčný bug. XSS ochrana je beztak v `html.escape` + CSP.
- **Zmeny**: `routes/chat.py` — odstrániť regex, ponechať `strip()`, length limit a `html.escape`.
- **Akceptácia**: test že správa `"Ahoj 👋 你好"` prejde nezmenená (po html.escape ekvivalentná).
- **Odhad**: 2 h
- **Závisí od**: 1.2 (bez silnej CSP je regex dodatočná poistka)

### 1.5 🟡 Password hashing — explicitný scrypt/argon2
- **Cieľ**: `werkzeug.security.generate_password_hash` default je `scrypt` od Werkzeug 3, ale v starších verziách `pbkdf2:sha256:600000`. Závisí na verzii — explicitne fixnúť.
- **Zmeny**: `models.py` alebo `database_operations.py:UserOperations.create_user` — `generate_password_hash(pw, method='scrypt')`. Poznámka: staré hashe ostanú funkčné (werkzeug auto-detect), ale nový hash sa vytvorí pri ďalšej zmene hesla.
- **Akceptácia**: nový user má hash začínajúci `scrypt:`.
- **Odhad**: 2 h

### 1.6 🟡 PII v logoch
- **Cieľ**: `enhanced_logging.py` loguje email — GDPR riziko pri incident response / log leaks.
- **Zmeny**: `enhanced_logging.py` — logovať len `user_id`. Pridať config flag `LOG_PII=false` pre dev override.
- **Akceptácia**: `grep -r "email" logs/` po cykle requestov nevracia emaily.
- **Odhad**: 2 h

---

## Fáza 2 — Stabilita (4–6 dní)

### 2.1 🔴 Streaming odpovedí z OLLAMA
- **Cieľ**: Aktuálne worker blokovaný 10–120 s na jeden chat request. Pri 4 workeroch stačí 4 pomalé requesty na odrezanie služby. Streaming = kratšia percepčná latencia a flexibilnejší timeout.
- **Zmeny**:
  - `ollama_client.py` — metóda `chat_stream(model, messages) -> Iterator[dict]` (už pravdepodobne existuje, ale nie je použitá v routes).
  - `routes/chat.py` — nový endpoint `/api/messages/stream` vracajúci `text/event-stream` (SSE). Starý `/api/messages` zachovať pre kompatibilitu.
  - `static/js/chat.js` — `EventSource` namiesto `fetch().then(json)`. Progresívny render.
  - Perzistencia AI správy až po dokončení streamu (on final event).
- **Akceptácia**: E2E test — prvý token viditeľný v UI do 2 s; plný worker block skracuje sa na dobu network I/O, nie LLM inference.
- **Odhad**: 2 d

### 2.2 🟠 Redis backend pre rate limiter
- **Cieľ**: `RATELIMIT_STORAGE_URL=memory://` znamená limit per-worker. Pri gunicorn `--workers 4` sa skutočný limit znásobí 4×.
- **Zmeny**:
  - `docker-compose.yml` — pridať `redis:7-alpine` službu.
  - `.env.example` — `RATELIMIT_STORAGE_URL=redis://redis:6379/0`.
  - `DEPLOYMENT.md` — poznámka že bez Redis je rate limit per-worker.
- **Akceptácia**: s 4 workermi a login limitom 5/min je 5. pokus z rovnakej IP blokovaný (nie 20.).
- **Odhad**: 4 h

### 2.3 🟠 Bulk delete ako jeden SQL
- **Cieľ**: `routes/chat.py:273` robí N-krát `delete_chat` v loope. Pri 50 chatoch = 50 roundtripov + 50 commitov = neúmerná záťaž a dlhé zamknutie.
- **Zmeny**: `database_operations.py:ChatOperations.bulk_delete_chats(chat_ids, user_id)` — jeden `DELETE FROM chats WHERE id IN (...) AND user_id = ?` v transakcii. Cascade zmaže aj messages (musí byť `ondelete='CASCADE'` v FK — overiť v `models.py`).
- **Akceptácia**: benchmark 50 chatov: pred zmenou X ms → po zmene <10 % X; správanie pri cudzom chat_id ostáva rovnaké (ignoruje sa).
- **Odhad**: 3 h
- **Závisí od**: 0.3 (ak treba pridať cascade, ide cez migráciu)

### 2.4 🟠 N+1 v `api_send_message` — `len(chat.messages)`
- **Cieľ**: `routes/chat.py:390` — `len(chat.messages)` načíta **celú** tabuľku správ iba pre count pri auto-generovaní titulu.
- **Zmeny**: použiť existujúci pattern z `get_user_chats_with_message_counts` alebo `db.session.query(func.count(Message.id)).filter_by(chat_id=chat_id).scalar()`.
- **Akceptácia**: SQL log pri send_message neobsahuje `SELECT * FROM messages WHERE chat_id = X` (len COUNT).
- **Odhad**: 1 h

### 2.5 🟡 Timeouty a circuit breaker pre OLLAMA
- **Cieľ**: Keď je OLLAMA server dole/pomalý, request visí 120 s. Opakované pokusy = cascade failure.
- **Zmeny**:
  - `ollama_client.py` — konfigurovateľný per-request timeout (zostáva 120 s default, ale cez config).
  - Nový `circuit_breaker.py` — in-memory per-host counter; po 5 failures v 60 s → 30 s "open" stav, requesty odmietnuté okamžite s 503.
  - Integrácia v `routes/chat.py` a `routes/api.py`.
- **Akceptácia**: simulovaný 5× timeout → 6. request vráti 503 do 10 ms.
- **Odhad**: 1 d

### 2.6 🟡 Graceful shutdown
- **Cieľ**: Pri SIGTERM (Docker restart) otvorené OLLAMA streamy sa ukončia abruptne, čiastočná AI odpoveď sa nestratí ale ani neuloží.
- **Zmeny**:
  - Signal handler v `app.py` — flush pending messages, close OLLAMA sessions.
  - Gunicorn `--graceful-timeout 30`.
  - `Dockerfile` — `STOPSIGNAL SIGTERM`.
- **Akceptácia**: `docker-compose stop` počas aktívneho chatu uloží aspoň čiastočnú AI odpoveď alebo user-friendly chybové hlásenie.
- **Odhad**: 4 h
- **Závisí od**: 2.1

---

## Fáza 3 — Výkon (3–5 dní)

### 3.1 🟠 Connection pool pre OllamaClient
- **Cieľ**: Aktuálne `with OllamaClient(host) as client` vytvára novú `requests.Session` per request → TCP handshake + prípadne TLS pri každom volaní.
- **Zmeny**:
  - Nový `ollama_pool.py` — thread-safe dict `{host: OllamaClient}` s TTL (napr. 10 min idle timeout) a max size (LRU eviction).
  - `routes/chat.py`, `routes/api.py` — získavať klienta cez `pool.get(host)`.
  - Health check: pri `ConnectionError` vypnúť klienta z poolu.
- **Akceptácia**: benchmark 100 sekvenčných requestov na rovnaký host: >30 % zníženie latencie po prvom.
- **Odhad**: 1 d
- **Závisí od**: 2.1 (aby sa pool správal dobre aj so streamingom)

### 3.2 🟠 Response cache pre `/api/models`
- **Cieľ**: Zoznam modelov sa zmení zriedka (pri `ollama pull`), ale dotazuje sa pri každom načítaní chat stránky.
- **Zmeny**:
  - Nový `response_cache.py` — `@cached(ttl=300, key_func=lambda: host)` dekorátor. In-memory (per worker; pre multi-worker stačí Redis-backed, ale modely sú lacný request).
  - Aplikovať na `routes/api.py:get_models` a `/api/test-connection`.
  - Invalidácia: manuálny endpoint `POST /api/models/refresh` (admin-only).
- **Akceptácia**: druhý GET /api/models do 5 min nespraví HTTP call na OLLAMA (log check).
- **Odhad**: 4 h

### 3.3 🟡 Index audit + EXPLAIN
- **Cieľ**: CLAUDE.md tvrdí existenciu `idx_chats_user_updated`, `idx_messages_chat_created` — overiť v `models.py` a cez `EXPLAIN QUERY PLAN` pre hot queries.
- **Zmeny**:
  - Overiť `models.py` `__table_args__`. Ak chýbajú → pridať + migrácia.
  - Hot queries: `get_user_chats_with_message_counts`, `get_latest_messages`, `get_chat_messages` — overiť že používajú index (nie `SCAN TABLE`).
- **Akceptácia**: `EXPLAIN QUERY PLAN` pre každú hot query ukazuje `USING INDEX`.
- **Odhad**: 3 h
- **Závisí od**: 0.3

### 3.4 🟡 Tokenizácia kontextu
- **Cieľ**: `CONVERSATION_HISTORY_LIMIT=10` posledných správ môže pri dlhých textoch prekročiť context window modelu → truncation alebo error z OLLAMA.
- **Zmeny**:
  - `pyproject.toml` — `tiktoken` alebo lighter alternatíva.
  - `routes/chat.py:api_send_message` — orezávať konverzáciu podľa token countu (napr. 4000 tokenov), nie podľa počtu správ.
  - Config `MAX_CONTEXT_TOKENS` (default 4000, overridable per model).
- **Akceptácia**: dlhý chat (20 × 500 slov) neskončí `context length exceeded` z OLLAMA.
- **Odhad**: 4 h

### 3.5 🟡 Gunicorn worker tuning
- **Cieľ**: OLLAMA requesty sú I/O bound (čakanie na LLM). Sync workers držia 1 request naraz; gevent zvládne stovky.
- **Zmeny**:
  - `pyproject.toml` (production extra) — pridať `gevent`.
  - `DEPLOYMENT.md` + `docker-compose.yml` — `gunicorn --worker-class gevent --workers 2 --worker-connections 1000`.
  - Overiť kompatibilitu s SQLAlchemy session (scoped session per greenlet).
- **Akceptácia**: load test 50 concurrent chat requestov: p95 latencia nižšia než so sync 4 workers.
- **Odhad**: 1 d
- **Závisí od**: 2.1, 3.1

### 3.6 🟢 Frontend — marked + DOMPurify
- **Cieľ**: Custom markdown renderer v `static/js/chat.js` je ~100 riadkov regex. `node_modules/` už pravdepodobne obsahuje marked.
- **Zmeny**:
  - `static/js/chat.js` — `marked.parse(content)` → `DOMPurify.sanitize(html)`.
  - `templates/chat.html` — include scriptov z `node_modules` alebo CDN (+ SRI hash, pozor na CSP).
- **Akceptácia**: tabuľky, code blocks, linky renderujú správne; žiadne nové CSP violations.
- **Odhad**: 4 h
- **Závisí od**: 1.2

---

## Fáza 4 — Produkčná pripravenosť (voliteľné, 3–5 dní)

### 4.1 🟡 PostgreSQL support
- **Cieľ**: SQLite nevhodný pri >10 súbežných používateľoch (database locked errors).
- **Zmeny**:
  - `pyproject.toml` — `psycopg[binary]` ako optional dependency.
  - `docker-compose.yml` — PostgreSQL service.
  - `models.py` — odstrániť SQLite-specific pragmas z hot path (alebo podmienené spustenie).
  - `DEPLOYMENT.md` — sekcia PostgreSQL setup.
- **Akceptácia**: plný test suite beží aj proti PostgreSQL; migrácie fungujú.
- **Odhad**: 1 d
- **Závisí od**: 0.3

### 4.2 🟡 Metrics + health endpoint
- **Cieľ**: Produkčný monitoring vyžaduje `/health` a metriky (latencia, error rate, OLLAMA availability).
- **Zmeny**:
  - Nový `routes/health.py` — `/health` (liveness), `/health/ready` (readiness s DB + OLLAMA check), `/metrics` (Prometheus format, ak je potreba).
  - `prometheus-flask-exporter` alebo custom counters.
- **Akceptácia**: `/health/ready` vracia 503 keď je DB nedostupná, 200 inak.
- **Odhad**: 4 h

### 4.3 🟢 Chat export (JSON/Markdown)
- **Cieľ**: User data portability (GDPR + user-requested feature zo `zadanie.md`).
- **Zmeny**: `routes/chat.py:/api/chats/<id>/export?format=md|json`.
- **Akceptácia**: download zachováva celý chat vrátane metadát.
- **Odhad**: 4 h

### 4.4 🟢 Full-text search správ
- **Cieľ**: Pri desiatkach chatov user nevie nájsť staršiu konverzáciu.
- **Zmeny**: SQLite FTS5 virtual table (alebo PostgreSQL `tsvector` v 4.1), endpoint `/api/search?q=`.
- **Akceptácia**: search "python" nájde všetky chat-y obsahujúce slovo v správach.
- **Odhad**: 1 d
- **Závisí od**: 0.3

---

## Celkový odhad a sekvencia

| Fáza | Rozsah | Odhad | Kritická cesta |
|------|--------|-------|----------------|
| 0    | Hygiena | 1–2 d | 0.1 → 0.2 → 0.3 |
| 1    | Bezpečnosť | 3–5 d | 1.1 ∥ 1.2 ∥ 1.3, potom 1.4–1.6 |
| 2    | Stabilita | 4–6 d | 2.1 → 2.6, ostatné paralelne |
| 3    | Výkon | 3–5 d | 3.1 ← 2.1, 3.2–3.6 paralelne |
| 4    | Produkčné | 3–5 d | voliteľné |

**Spolu**: ~14–23 dní práce pre plnú realizáciu (fázy 0–3). Pri 1 developerovi part-time to reálne znamená 4–8 týždňov.

## Princípy postupu

1. **Po každej úlohe commit + push** (podľa globálnej CLAUDE.md).
2. **Test pred merge** — každá úloha má pridať/aktualizovať testy.
3. **Žiadne skratky v bezpečnosti** — Fázu 1 neodkladať kvôli výkonu.
4. **Feature flag pre veľké zmeny** — streaming endpoint paralelne so starým, aby sa dal rýchlo vypnúť.
5. **Aktualizovať CLAUDE.md po každej fáze** — aby ďalšie sessiony mali aktuálny kontext.

## Nerozhodnuté otázky (na diskusiu s userom)

- Cieľová škála deployment (1 user / desiatky / stovky)? Ovplyvňuje prioritu 4.1 a 2.2.
- Je HTTPS/doména už nastavená, alebo je to lokálne dev prostredie? Ovplyvňuje prioritu 1.3 a CSP.
- Má OLLAMA bežať lokálne (localhost) alebo na samostatnom serveri? Ovplyvňuje SSRF whitelist v 1.1.
- Viacuserový scenár alebo single-user self-hosted? Ovplyvňuje rozsah GDPR (1.6, 4.3).
