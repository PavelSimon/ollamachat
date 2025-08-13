# OLLAMA Chat Deployment Guide

Tento dokument popisuje ako nasadiť OLLAMA Chat aplikáciu do produkcie.

## Požiadavky

- Docker a Docker Compose
- OLLAMA server (môže bežať v Docker kontajneri)
- Python 3.8+ (pre lokálne nasadenie)

## Docker Deployment (Odporúčané)

### 1. Príprava

```bash
# Klonujte repository
git clone <repository-url>
cd ollama-chat

# Vytvorte .env súbor
cp .env.example .env
```

### 2. Konfigurácia

Upravte `.env` súbor:

```bash
# Nastavte produkčné hodnoty
FLASK_ENV=production
SECRET_KEY=your-very-secure-secret-key-here
DATABASE_URL=sqlite:///instance/chat.db
```

### 3. Spustenie s Docker Compose

```bash
# Spustenie všetkých služieb (OLLAMA Chat + OLLAMA server)
docker-compose up -d

# Alebo len OLLAMA Chat (ak máte externý OLLAMA server)
docker-compose up -d ollama-chat
```

### 4. Inicializácia OLLAMA modelov

```bash
# Pripojte sa k OLLAMA kontajneru
docker exec -it ollama-chat_ollama_1 ollama pull gpt-oss:20b

# Alebo iný model
docker exec -it ollama-chat_ollama_1 ollama pull llama2:latest
```

## Lokálne Production Deployment

### 1. Inštalácia závislostí

```bash
# Nainštalujte uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Nainštalujte závislosti
uv sync --extra production
```

### 2. Konfigurácia

```bash
# Vytvorte .env súbor
cp .env.example .env

# Upravte konfiguráciu
export FLASK_ENV=production
export SECRET_KEY="your-secure-secret-key"
```

### 3. Inicializácia databázy

```bash
uv run python -c "from app import init_db; init_db()"
```

### 4. Spustenie s Gunicorn

```bash
# Produkčné spustenie
uv run gunicorn --bind 0.0.0.0:5000 --workers 4 app:app

# S logovaním
uv run gunicorn --bind 0.0.0.0:5000 --workers 4 --access-logfile - --error-logfile - app:app
```

## Nginx Reverse Proxy (Voliteľné)

Vytvorte `/etc/nginx/sites-available/ollama-chat`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/ollama-chat/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

Aktivujte konfiguráciu:

```bash
sudo ln -s /etc/nginx/sites-available/ollama-chat /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## SSL/HTTPS (Odporúčané)

### S Let's Encrypt

```bash
# Nainštalujte certbot
sudo apt install certbot python3-certbot-nginx

# Získajte SSL certifikát
sudo certbot --nginx -d your-domain.com

# Automatické obnovenie
sudo crontab -e
# Pridajte: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Monitorovanie a Zálohovanie

### Zálohovanie databázy

```bash
# Vytvorte zálohu SQLite databázy
cp instance/chat.db backups/chat_$(date +%Y%m%d_%H%M%S).db

# Automatické zálohovanie (cron)
0 2 * * * cp /path/to/ollama-chat/instance/chat.db /path/to/backups/chat_$(date +\%Y\%m\%d_\%H\%M\%S).db
```

### Loggovanie

```bash
# Sledovanie logov
docker-compose logs -f ollama-chat

# Alebo pre lokálne nasadenie
tail -f /var/log/ollama-chat/app.log
```

## Bezpečnosť

### Firewall

```bash
# Povoľte len potrebné porty
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

### Aktualizácie

```bash
# Pravidelne aktualizujte systém
sudo apt update && sudo apt upgrade

# Aktualizujte Docker images
docker-compose pull
docker-compose up -d
```

## Troubleshooting

### Časté problémy

1. **Databáza sa nevytvorí**
   ```bash
   # Skontrolujte oprávnenia
   ls -la instance/
   # Vytvorte manuálne
   uv run python -c "from app import init_db; init_db()"
   ```

2. **OLLAMA server nedostupný**
   ```bash
   # Skontrolujte pripojenie
   curl http://localhost:11434/api/tags
   # Skontrolujte nastavenia v aplikácii
   ```

3. **Chyby oprávnení**
   ```bash
   # Nastavte správne oprávnenia
   chown -R www-data:www-data /path/to/ollama-chat
   chmod -R 755 /path/to/ollama-chat
   ```

### Logy

```bash
# Docker logy
docker-compose logs ollama-chat

# Aplikačné logy
tail -f /var/log/ollama-chat.log

# Nginx logy
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

## Performance Tuning

### Gunicorn nastavenia

```bash
# Viac workerov pre vyšší traffic
gunicorn --workers 8 --worker-class gevent --worker-connections 1000 app:app

# Pre CPU-intensive úlohy
gunicorn --workers 4 --worker-class sync app:app
```

### Databáza optimalizácia

```sql
-- SQLite optimalizácia
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=10000;
PRAGMA temp_store=memory;
```

## Škálovanie

Pre vysoký traffic zvážte:

1. **Load balancer** (nginx, HAProxy)
2. **Databáza** (PostgreSQL namiesto SQLite)
3. **Redis** pre session storage
4. **CDN** pre statické súbory

## Podpora

Pre problémy s nasadením:
1. Skontrolujte logy
2. Overte konfiguráciu
3. Otvorte issue v repository