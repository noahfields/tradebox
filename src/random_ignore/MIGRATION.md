# Docker & PostgreSQL Migration Summary

## Overview
Tradebox has been successfully migrated to run in Docker with PostgreSQL as the primary database backend. This provides better production readiness, scalability, and simplified deployment.

## Files Created

### Docker Configuration
- **Dockerfile** - Multi-purpose image for runners and API services
- **docker-compose.yml** - Service orchestration (PostgreSQL, runners, API)
- **.dockerignore** - Optimize Docker build context
- **.env.example** - Template for environment configuration
- **DOCKER.md** - Complete Docker deployment guide

### Documentation Updates
- **README.md** - Updated with Docker quick-start section
- **.github/copilot-instructions.md** - Added Docker and PostgreSQL sections

## Files Modified

### Configuration
- **src/config-default-must-rename.py**
  - Now uses `python-dotenv` to read from `.env` file
  - DATABASE_URL points to PostgreSQL
  - LOG_DIR defaults to `/app/logs` for Docker

### Dependencies
- **pyproject.toml**
  - Added `psycopg2-binary>=2.9.0` (PostgreSQL driver)
  - Added `python-dotenv>=1.0.0` (environment config)
  - Added `flask>=2.3.0` (Flask server)
  - Updated Python requirement to `>=3.11`

### Database Layer
- **src/database.py**
  - Replaced `sqlite3` with `psycopg2`
  - Connection uses `config.DATABASE_URL` (PostgreSQL connection string)
  - Removed SQLite-specific code (no DB_FILE variable)
  - Updated delete_database() to drop tables via DROP TABLE IF EXISTS
  - JSON operations now use PostgreSQL operators (`->`, `->>`)
  - Timestamp fields use `DOUBLE PRECISION` instead of `REAL`
  - All cursor operations now use `DictCursor` for better dict access

## Key Changes

### Database Schema Changes
- `SERIAL PRIMARY KEY` for auto-increment (PostgreSQL) instead of `INTEGER PRIMARY KEY ASC`
- `JSONB` columns for JSON data (already in schema, now properly used)
- `DOUBLE PRECISION` for float timestamps
- JSON queries use `json_field -> 'key'` and `json_field ->> 'key'` instead of `json_extract()`

### Configuration Management
- Environment variables in `.env` control all settings
- No need to rename `config.py` files - uses `.env` directly
- Docker services pass environment variables to containers
- PostgreSQL connection details configurable via `.env`

### Service Architecture
```
postgresql:5432 (postgres_data volume)
    ↓
tradebox_runners (ThreadPoolExecutor, 4 runners)
    ↓
tradebox_api (Flask API on :5555)
    ↓
Logs to ./logs (mounted volume)
```

## Running Tradebox

### With Docker (Recommended)
```bash
cp .env.example .env
nano .env  # Edit credentials
docker-compose up -d
docker-compose logs -f  # View logs
```

### Without Docker (Legacy)
```bash
cp src/config-default-must-rename.py src/config.py
nano src/config.py  # Edit credentials
python -m src.runners  # In one terminal
python src/order_trigger_server.py  # In another terminal
```

## Environment Variables (.env)

**Database:**
- DATABASE_URL - PostgreSQL connection string
- DB_USER, DB_PASSWORD, DB_NAME, DB_PORT

**Robinhood:**
- ROBINHOOD_USERNAME
- ROBINHOOD_PASSWORD

**API:**
- DEV_IP, DEV_PORT, DEV_DEBUG

**Logging:**
- LOG_LEVEL, FILE_LOGGING, STDOUT_LOGGING, LOG_DIR

**Refresh Intervals:**
- MARKET_DATA_REFRESH_INTERVAL
- OPEN_POSITIONS_REFRESH_INTERVAL
- BROKER_ORDERS_REFRESH_INTERVAL
- MAXIMUM_INTERVAL

## Benefits

✅ **Containerization** - Consistent environment across dev/prod  
✅ **PostgreSQL** - Better scalability, JSONB support, production-ready  
✅ **Environment config** - No renaming required, 12-factor app compliant  
✅ **Health checks** - Services wait for DB readiness  
✅ **Volume persistence** - Database data survives container restarts  
✅ **Easy scaling** - Can run multiple runner containers with different configs  
✅ **Better logging** - Consolidated logs from all services  

## Upgrade Path for Existing Users

If you were running Tradebox with SQLite3:

1. Backup your SQLite database: `cp tradebox.db tradebox.db.backup`
2. Export data if needed via SQL dumps
3. Follow the Docker setup in DOCKER.md
4. PostgreSQL will initialize fresh (data migration not automated)

## Next Steps

1. Create `.env` file with your credentials
2. Run `docker-compose up -d`
3. Verify services: `docker-compose ps`
4. Check logs: `docker-compose logs runners`
5. Access API at http://localhost:5555

See [DOCKER.md](DOCKER.md) for full documentation and troubleshooting.
