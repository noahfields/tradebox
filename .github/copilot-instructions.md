# Tradebox AI Coding Instructions

## Project Overview
Tradebox is a Python-based stock option trading platform with **Robinhood API integration**, real-time market data synchronization, and TUI (Textual) console interfaces. The system is split into background runner processes that sync data and a Flask API server for order execution.

**Status**: Pre-production (July 2024) – Not yet deployed.

## Architecture & Data Flow

### Core Components
- **[runners.py](../src/runners.py)**: Concurrent background workers using `ThreadPoolExecutor`. Each runner loops indefinitely, refreshes data on intervals, and adjusts `adjusted_interval` based on success/failure (backoff pattern). It is necessary that the failure of one runner does not result in runners.py exiting: all runners must handle all exceptions, and continue looping while the others continue.
- **[system_management.py](../src/system_management.py) will contain Python methods for creating, deleting, activating, deactivating, and starting and stopping runners systemd service on Debian.
- **[robinhood_api.py](../src/robinhood_api.py)**: Wrapper around `robin-stocks` library with API verification using `API_VERIFICATION_DEFAULT_KEYSETS` (detects breaking Robinhood API changes).
- **[database.py](../src/database.py)**: Postgres server gateway. Stores runner state, option positions, broker orders, and trigger orders. Uses `still_alive` flag pattern for soft deletes during refreshes.
- **[order_trigger_server.py](../src/order_trigger_server.py)**: Flask API server (`wsgi:app`). Endpoint `/orders/execute/<order_id>` accepts POST/GET to execute trades.
- **[console_desktop.py](../src/console_desktop.py)**: Textual TUI for monitoring runners, viewing positions, and managing orders. Two tabs: Main (positions, runner status) and System Management.

### Data Synchronization Pattern
```
Robinhood API → robinhood_api.py → database (JSON + metadata) → TUI displays
                     ↓
           verify_api_key_match()
           (detects API schema changes)
```

Runners use `still_alive=1` marking: Set all rows to 0, refresh API data marking new rows as 1, delete rows still 0 (stale).

## Project Conventions & Patterns

### Code Style
- **No comments** – code must be self-explanatory (see TODO.md)
- **Type hints** on all function parameters and return values
- **Capitalized globals** only: `SRC_DIR`, `REPO_DIR` (see [globals.py](../src/globals.py))
- **Tab indentation** (configured in pyproject.toml: `indent-style = "tab"`)
- **79-character line length** (pyproject.toml: `line-length = 79`)

### Logging Levels (Project-Specific)
- **DEBUG**: Development milestones, temporary fixes
- **INFO**: API call data dumps (raw Robinhood responses)
- **WARNING**: Unexpected but non-breaking
- **ERROR**: Breaks functionality, sent to notifications
- **CRITICAL**: System failure, sent to notifications
- **Important**: Log calls one at a time to prevent notification spam

### Database Schema Patterns
- **JSONB columns** store raw API responses for analysis
- **`still_alive` flag** (0/1) marks stale rows during refresh cycles
- **`last_update_epoch_time`** tracks freshness
- Tables: `runners`, `open_option_positions`, `open_option_positions_market_data`, `open_broker_option_orders`, `open_broker_option_orders_market_data`, `trigger_option_orders`

### Runner Management Pattern
```python
# In loop_runner():
1. Get runner state from DB
2. Check if active; if not, sleep and continue
3. Mark as failed preemptively
4. Execute runner function (e.g., update_open_option_positions())
5. If success: decrease adjusted_interval (min=default_interval), update DB
6. If failure: increase adjusted_interval (max=MAXIMUM_INTERVAL), sleep 2x, retry
```

## Database Layer
**PostgreSQL (via Docker)** replaces SQLite3. All queries use `psycopg2`:
- Connection: `psycopg2.connect(config.DATABASE_URL)`
- Use `DictCursor` for row-as-dict access (see `get_all_runners_status()`)
- JSON functions: PostgreSQL `->`, `->>` operators (not `json_extract()`)
- `DOUBLE PRECISION` for float timestamps (not SQLite `REAL`)

## Docker Deployment
- **Dockerfile**: Single image for runners and API (CMD varies by service)
- **docker-compose.yml**: Orchestrates PostgreSQL, runners, and API containers
- **Environment-based config**: `.env` file drives all settings (DATABASE_URL, credentials, intervals)
- **Service startup order**: PostgreSQL health check gates runners/API startup
- **Volumes**: `postgres_data` for DB persistence, `./logs` for app logs

### Docker Usage
```bash
docker-compose up -d                 # Start all services
docker-compose logs -f runners       # View runner logs
docker-compose exec postgres psql -U tradebox tradebox  # Connect to DB
```

## Critical Integration Points
Before using new API response fields:
1. Add sample response to `API_VERIFICATION_DEFAULT_KEYSETS[key_name]` in [robinhood_api.py](../src/robinhood_api.py)
2. Call `verify_api_key_match()` in each API function
3. If schema mismatch: logs `keys_only_in_DEFAULT` and `keys_only_in_LIVE` for debugging

### Configuration
Edit and **rename** [config-default-must-rename.py](../src/config-default-must-rename.py) → `config.py`:
- Robinhood credentials
- Pushover API tokens (notifications)
- Refresh intervals: `MARKET_DATA_REFRESH_INTERVAL`, `OPEN_POSITIONS_REFRESH_INTERVAL`, `BROKER_ORDERS_REFRESH_INTERVAL`
- Database/log paths

### Flask Server Timeout
**Critical for Robinhood API calls** (can take >5 min):
```bash
gunicorn --timeout 600 --workers 3 --bind unix:tradebox.sock -m 007 wsgi:app
```

## Textual TUI Specifics
- CSS styling in `.tcss` files in 'tcss/' (e.g., [console_desktop.tcss](../src/tcss/console_desktop.tcss))
- Modal dialogs extend `ModalScreen`
- DataTable refreshes via `set_interval()` in `on_mount()`
- Color coding: Use `[green]...[/green]` and `[red]...[/red]` inline markup for P/L display

## File Organization
```
src/
├── runners.py           # Background worker loops
├── robinhood_api.py     # API wrapper + verification
├── database.py          # PostgreSQL gateway
├── order_trigger_server.py  # Flask API
├── console_desktop.py   # Main TUI
├── log.py              # Logger setup (rotating files)
├── config-default-must-rename.py  # Credentials template
└── *.tcss              # Textual CSS
```

Old code (`old_*.py`) preserved for reference; do not import.
Ignore files in 'src/random_ignore/': they are scratchpads.

## Development Workflows
1. **Database reset**: `database.delete_database()` + `create_database_tables()`
2. **Runner status**: Query `runners` table; check `active`, `adjusted_interval`, `last_successful_update_epoch_time`
3. **Logging output**: Check `logs/` directory (rotated, max 10 backups per file)
4. **Test trade execution**: Use [old_console.py](../old_console.py) pattern or Flask endpoint `/orders/execute/<order_id>`

## Known Limitations & TODOs
- Emergency order fills (50% bid/ask discount) are only partially implemented
- Trigger orders table exists but execution engine not fully wired
- Mobile TUI version (console_mobile.py) not started
- Trailing orders and bracket orders incomplete
- Must handle MFA codes for initial Robinhood login. Robinhood doesn't use MFA codes anymore.

---

**Update this file** if discovering new patterns or API breaking changes. Reference files directly via `[filename](../src/filename.py)` links.
