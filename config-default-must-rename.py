"""Configuration settings for Tradebox."""

# WARNING
# YOU MUST CHANGE THE NAME OF THIS FILE to 'config.py'
# FOR TRADEBOX TO RUN

# URL
# if in development environment, leave as is
# if in production, please change to your full public domain name (ideally using https instead of http)
TRADEBOX_APP_ADDRESS = 'http://127.0.0.1/'  # must end with '/'

# ENTER ROBINHOOD USERNAME AND PASSWORD
ROBINHOOD_USERNAME = ''
ROBINHOOD_PASSWORD = ''
ROBINHOOD_SESSION_EXPIRES_IN = '172800'  # string (seconds)

# PUSHOVER NOTIFICATION SETTINGS # Requires a Pushover account for long term use (pushover.net)
# Available on desktop, Android, iPhone
# This allows you to receive real-time notifications of trade statuses
# To receive notifications, you will need to install the Pushover App on a phone or computer
PUSHOVER_USER_TOKEN = '' # Pushover User Key (available on main page of pushover.net when logged in)
PUSHOVER_API_TOKEN = '' # Pushover API Token/Key (under "Your Applications", you need to set up an application for this key)

# DEBUG ENVIRONMENT SETTINGS
DEV_IP='127.0.0.1'
DEV_PORT=5555
DEV_DEBUG=True

# change only if needed (for example, to save database when re-cloning tradebox application)
# recommended to place these one level below your git cloned directory to preserve database integrity
# across git clones for future updates
DATABASE_DIR = '.'
DATABASE_NAME = 'db.sqlite3'  # change only if needed

# LOGS
# same advice as database directories
LOG_PARENT_DIR = '.'
LOG_DIR_NAME = 'logs'
