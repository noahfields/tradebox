# Tradebox Docker Deployment

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Robinhood account credentials

### Setup

1. **Clone the repository and navigate to the project:**
   ```bash
   cd tradebox
   ```

2. **Create environment file from template:**
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env` with your credentials:**
   ```bash
   nano .env
   ```
   
   At minimum, set:
   - `ROBINHOOD_USERNAME` - Your Robinhood email
   - `ROBINHOOD_PASSWORD` - Your Robinhood password
   - `DB_PASSWORD` - Strong PostgreSQL password
   - `PUSHOVER_USER_TOKEN` and `PUSHOVER_API_TOKEN` (optional for notifications)

4. **Start the services:**
   ```bash
   docker-compose up -d
   ```

5. **Verify services are running:**
   ```bash
   docker-compose ps
   ```

## Service Overview

### PostgreSQL Database
- Container: `tradebox_postgres`
- Default credentials in `.env`: `tradebox:tradebox_password`
- Data persisted in Docker volume: `postgres_data`
- Accessible on `localhost:5432` (configurable via `.env`)

### Runners
- Container: `tradebox_runners`
- Concurrent background workers syncing market data
- Auto-restarts on failure
- Logs available via: `docker-compose logs runners`

### Flask API Server
- Container: `tradebox_api`
- REST API for order execution
- Accessible on `http://localhost:5555`
- Logs available via: `docker-compose logs api`

## Common Commands

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f runners
docker-compose logs -f api
docker-compose logs -f postgres
```

### Connect to PostgreSQL
```bash
docker-compose exec postgres psql -U tradebox -d tradebox
```

### Stop services
```bash
docker-compose down
```

### Restart services
```bash
docker-compose restart
```

### Rebuild images (after code changes)
```bash
docker-compose up -d --build
```

## Configuration

### Environment Variables (.env)

**Database:**
- `DB_USER` - PostgreSQL username (default: `tradebox`)
- `DB_PASSWORD` - PostgreSQL password (default: `tradebox_password`)
- `DB_NAME` - Database name (default: `tradebox`)
- `DB_PORT` - PostgreSQL port (default: `5432`)

**Robinhood:**
- `ROBINHOOD_USERNAME` - Your email
- `ROBINHOOD_PASSWORD` - Your password

**Notifications (optional):**
- `PUSHOVER_USER_TOKEN` - Pushover user key
- `PUSHOVER_API_TOKEN` - Pushover API token

**Refresh Intervals (seconds):**
- `MARKET_DATA_REFRESH_INTERVAL` (default: `5`)
- `OPEN_POSITIONS_REFRESH_INTERVAL` (default: `5`)
- `BROKER_ORDERS_REFRESH_INTERVAL` (default: `30`)
- `MAXIMUM_INTERVAL` (default: `3`)

**Logging:**
- `LOG_LEVEL` - DEBUG, INFO, WARNING, ERROR, CRITICAL (default: `INFO`)
- `FILE_LOGGING` - 0 or 1 (default: `1`)
- `STDOUT_LOGGING` - 0 or 1 (default: `1`)

**Development:**
- `DEV_DEBUG` - 0 or 1 for Flask debug mode (default: `0`)

## Production Considerations

### Security
- Change all default credentials in `.env`
- Use environment-specific `.env` files (don't commit to git)
- Store `.env` securely with appropriate file permissions
- Use PostgreSQL user accounts with restricted privileges

### Scaling
- Adjust `max_workers` in `src/runners.py` for CPU-bound workloads
- Add more runner containers with different environment configs if needed

### Data Persistence
- Database data is stored in `postgres_data` Docker volume
- Backup regularly: `docker-compose exec postgres pg_dump -U tradebox tradebox > backup.sql`
- Restore from backup: `docker-compose exec -T postgres psql -U tradebox tradebox < backup.sql`

### Monitoring
- Access logs via `docker-compose logs`
- Monitor container health: `docker-compose ps`
- Set up external logging aggregation for production

## Troubleshooting

### Database connection fails
- Verify PostgreSQL is running: `docker-compose ps postgres`
- Check DATABASE_URL in container: `docker-compose exec api env | grep DATABASE_URL`
- View postgres logs: `docker-compose logs postgres`

### Runners not executing
- Check if runners container is healthy: `docker-compose ps runners`
- Verify Robinhood credentials in `.env`
- Check logs: `docker-compose logs runners`

### API server not responding
- Verify API is running: `docker-compose ps api`
- Check port binding: `docker-compose port api 5555`
- Test locally: `curl http://localhost:5555/`

### Out of memory
- Increase Docker memory limits in Docker Desktop settings
- Adjust runner worker count in `src/runners.py`

## Development Workflow

### Making code changes
1. Edit files locally
2. Rebuild images: `docker-compose up -d --build`
3. View logs: `docker-compose logs -f`

### Creating database migrations
1. Connect to DB: `docker-compose exec postgres psql -U tradebox tradebox`
2. Run migrations manually or via application startup

### Debugging
- Add `print()` statements (visible in logs)
- Set `LOG_LEVEL=DEBUG` in `.env`
- Use Python debugger with `docker-compose exec` for interactive debugging

## SSL Certificates & HTTPS Setup

### Development (HTTP on port 8898)
No certificate needed. Access the API via `http://localhost:8898`

### Production (HTTPS on port 443)

#### Option 1: Let's Encrypt (Recommended)

1. **Install Certbot locally** (on the host machine, not in Docker):
   ```bash
   # macOS
   brew install certbot
   
   # Ubuntu/Debian
   sudo apt-get install certbot
   
   # Or use Docker
   docker run -it --rm -v "$(pwd)/certs:/etc/letsencrypt" certbot/certbot certonly --manual --preferred-challenges dns -d yourdomain.com
   ```

2. **Generate certificate** (valid domain required):
   ```bash
   certbot certonly --standalone -d yourdomain.com
   ```
   This creates: `/etc/letsencrypt/live/yourdomain.com/{fullchain.pem,privkey.pem}`

3. **Mount certificates in Docker**:
   Update `.env`:
   ```
   DOMAIN_NAME=yourdomain.com
   SSL_CERT_DIR=./certs
   ```
   Copy certificates to `./certs/live/yourdomain.com/`:
   ```bash
   mkdir -p certs/live/yourdomain.com
   sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem certs/live/yourdomain.com/
   sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem certs/live/yourdomain.com/
   sudo chown -R $USER:$USER certs
   ```

4. **Restart nginx**:
   ```bash
   docker-compose restart nginx
   ```

5. **Renew before expiration** (every 90 days):
   ```bash
   certbot renew
   # Copy renewed certs back to ./certs
   ```

#### Option 2: Self-Signed Certificate (Testing Only)

For local testing without a valid domain:

```bash
# Generate self-signed cert
mkdir -p certs/live/localhost
openssl req -x509 -newkey rsa:4096 -keyout certs/live/localhost/privkey.pem \
  -out certs/live/localhost/fullchain.pem -days 365 -nodes \
  -subj "/C=US/ST=State/L=City/O=Org/CN=localhost"

# Update .env
DOMAIN_NAME=localhost

# Start services
docker-compose up -d
```

Access via `https://localhost:443` (accept untrusted certificate warning)

#### Option 3: Automated Renewal with Certbot in Docker

Run certbot as a separate container to auto-renew:

```bash
docker run -d \
  --name certbot \
  -v "$(pwd)/certs:/etc/letsencrypt" \
  -v "$(pwd)/certbot_www:/var/www/certbot" \
  certbot/certbot:latest \
  renew --webroot -w /var/www/certbot --quiet
```

### Certificate Directory Structure

```
certs/
├── live/
│   └── yourdomain.com/
│       ├── fullchain.pem   # Full cert chain
│       ├── privkey.pem     # Private key
│       ├── cert.pem        # Server certificate
│       └── chain.pem       # Intermediate certs
└── renewal/
    └── yourdomain.com.conf # Renewal config
```

### Nginx Configuration Notes

- `nginx.conf` listens on port **80** (HTTP) for ACME challenges and redirects to HTTPS
- `nginx.conf` listens on port **443** (HTTPS) for production traffic
- Development port **8898** is plain HTTP for local testing (no SSL)
- Proxy timeouts set to 600s to handle long Robinhood API calls

### Troubleshooting SSL

**Certificate not found:**
```bash
docker-compose logs nginx
# Check: /etc/letsencrypt/live/{DOMAIN_NAME}/fullchain.pem exists
```

**Port 443 already in use:**
```bash
# Find process
lsof -i :443

# Kill it or use different port in docker-compose.yml
```

**Mixed content warnings:**
- Ensure all API calls use HTTPS (not HTTP) in client code
- Check proxy headers in nginx.conf: `X-Forwarded-Proto`

## Additional Resources

- Robinhood API: https://github.com/jmfernandes/robin_stocks
- PostgreSQL Docs: https://www.postgresql.org/docs/
- Docker Compose Docs: https://docs.docker.com/compose/
- Let's Encrypt: https://letsencrypt.org/
- Nginx Reverse Proxy: https://nginx.org/en/docs/http/ngx_http_proxy_module.html
