"""Configuration settings for Tradebox."""

# WARNING
# YOU MUST CHANGE THE NAME OF THIS FILE to 'config.py'
# FOR TRADEBOX TO RUN

# URL
# if in development environment, leave as is
# if in production, please change to your full public domain name (ideally using https instead of http)
TRADEBOX_APP_ADDRESS = "https://127.0.0.1/"  # must end with '/'

# ENTER ROBINHOOD USERNAME AND PASSWORD
ROBINHOOD_USERNAME = ""
ROBINHOOD_PASSWORD = ""

# RUNNER REFRESH INTERVAL DEFAULTS (in seconds)
MARKET_DATA_REFRESH_INTERVAL = 5
OPEN_POSITIONS_REFRESH_INTERVAL = 5
BROKER_ORDERS_REFRESH_INTERVAL = 30
MAXIMUM_INTERVAL = 3

# PUSHOVER NOTIFICATION SETTINGS # Requires a Pushover account for long term use (pushover.net)
# Available on desktop, Android, iPhone
# This allows you to receive real-time notifications of trade statuses
# To receive notifications, you will need to install the Pushover App on a phone or computer
PUSHOVER_USER_TOKEN = ""
PUSHOVER_API_TOKEN = ""

# DEBUG ENVIRONMENT SETTINGS
DEV_IP="127.0.0.1"
DEV_PORT=5555
DEV_DEBUG=False

# change only if needed (for example, to save database when re-cloning tradebox application)
# recommended to place these one level below your git cloned directory to preserve database integrity
# across git clones for future updates
DATABASE_DIR = '..'
DATABASE_NAME = 'db.sqlite3'  # change only if needed

# LOGS
# same advice as database directories
LOG_DIR = '..'