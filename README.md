NOT PRODUCTION READY - JULY 24, 2024
PLEASE DO NOT USE

Tradebox is a Python-based stock option trading platform with Robinhood API integration and real-time market data synchronization.

**Documentation:**
- [Docker Deployment Guide](DOCKER.md) - Setup with Docker and PostgreSQL
- [Original README](#legacy) - Legacy notes below

## Quick Start with Docker

```bash
# Copy environment template
cp .env.example .env

# Edit with your Robinhood credentials
nano .env

# Start services (PostgreSQL, API, runners)
docker-compose up -d
```

Services will be available at:
- Flask API: http://localhost:5555
- PostgreSQL: localhost:5432

See [DOCKER.md](DOCKER.md) for full deployment documentation.

## Legacy Notes

For help setting up a server on Debian or Ubuntu without Docker:
https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-22-04

### Configuration
1. Edit `src/config-default-must-rename.py` with your credentials
2. Rename to `src/config.py`
3. Set Robinhood username and password
4. Configure Pushover tokens (optional for notifications)

### Running with Gunicorn
For production API deployment, use high timeout values since Robinhood API calls can take time:

```bash
gunicorn --timeout 600 --workers 3 --bind unix:tradebox.sock -m 007 wsgi:app
```

### Database
- Default: SQLite3 (file-based)
- Recommended for production: PostgreSQL (see Docker setup)

---

## Architecture

- **runners.py**: Background workers syncing market data via Robinhood API
- **database.py**: Data persistence layer (SQLite3 or PostgreSQL)
- **robinhood_api.py**: Robinhood API wrapper with schema verification
- **order_trigger_server.py**: Flask REST API for order execution
- **console_desktop.py**: Textual TUI for monitoring positions and runners