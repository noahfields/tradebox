"""Configuration settings for Tradebox."""

# WARNING
# YOU MUST CHANGE THE NAME OF THIS FILE to 'config.py'
# FOR TRADEBOX TO RUN

# URL
TRADEBOX_APP_ADDRESS = 'http://127.0.0.1/'  # must end with '/'

# ENTER ROBINHOOD USERNAME AND PASSWORD
ROBINHOOD_USERNAME = ''
ROBINHOOD_PASSWORD = ''
ROBINHOOD_SESSION_EXPIRES_IN = '172800'  # string (seconds)

# TRADE EMAIL NOTIFICATION SETTINGS
SMTP_USERNAME = ''
SMTP_PASSWORD = ''
SMTP_SERVER = ''
SMTP_PORT = 465  # port for Gmail SSL if using Gmail's SMTP servers
NOTIFICATION_ADDRESS = ''

# DEBUG ENVIRONMENT SETTINGS
DEV_IP='127.0.0.1'
DEV_PORT=5555
DEV_DEBUG=True

# change only if needed (for example, to save database when re-cloning tradebox application)
DATABASE_DIR = '.'
DATABASE_NAME = 'db.sqlite3'  # change only if needed

# LOGS
LOG_PARENT_DIR = '.'
LOG_DIR_NAME = 'logs'
