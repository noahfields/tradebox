from dotenv import load_dotenv
import os

# Load environment variables from the .env file (if present)
load_dotenv()

# URL
# if in development environment, leave as is
# if in production, please change to your full public domain name (ideally using https instead of http)
TRADEBOX_APP_ADDRESS = 'http://127.0.0.1/'  # must end with '/'

# ENTER ROBINHOOD USERNAME AND PASSWORD
ROBINHOOD_USERNAME = os.getenv("ROBINHOOD_USERNAME")
ROBINHOOD_PASSWORD = os.getenv("ROBINHOOD_PASSWORD")

# PUSHOVER NOTIFICATION SETTINGS # Requires a Pushover account for long term use (pushover.net)
# Available on desktop, Android, iPhone
# This allows you to receive real-time notifications of trade statuses
# To receive notifications, you will need to install the Pushover App on a phone or computer
PUSHOVER_USER_TOKEN = os.getenv("PUSHOVER_USER_TOKEN") # Pushover User Key (available on main page of pushover.net when logged in)
PUSHOVER_API_TOKEN = os.getenv("PUSHOVER_API_TOKEN") # Pushover API Token/Key (under "Your Applications", you need to set up an application for this key)

# DEBUG ENVIRONMENT SETTINGS
DEV_FLASK_IP='127.0.0.1'
DEV_FLASK_PORT=5555
DEV_FLASK_DEBUG=True

# Refresh Intervals (seconds)
MARKET_DATA_REFRESH_INTERVAL=os.getenv("MARKET_DATA_REFRESH_INTERVAL")
OPEN_POSITIONS_REFRESH_INTERVAL=os.getenv("OPEN_POSITIONS_REFRESH_INTERVAL")
BROKER_ORDERS_REFRESH_INTERVAL=os.getenv("BROKER_ORDERS_REFRESH_INTERVAL")
MAXIMUM_REFRESH_INTERVAL=os.getenv("MAXIMUM_REFRESH_INTERVAL")
RUNNER_FAILURE_ADJUSTMENT=os.getenv("RUNNER_FAILURE_ADJUSTMENT", 5)
RUNNER_SUCCESS_ADJUSTMENT=os.getenv("RUNNER_SUCCESS_ADJUSTMENT", 1)

# change only if needed (for example, to save database when re-cloning tradebox application)
# recommended to place these one level below your git cloned directory to preserve database integrity
# across git clones for future updates

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT")
DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@localhost:{DB_PORT}/{DB_NAME}"

# LOGS
# same advice as database directories
FILE_LOGGING = os.getenv("FILE_LOGGING")
STDOUT_LOGGING = os.getenv("STDOUT_LOGGING")
LOG_LEVEL = os.getenv("LOG_LEVEL")


#NOT SURE IF NEEDED?
LOG_PARENT_DIR = '.'
LOG_DIR_NAME = 'logs'