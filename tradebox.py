"""Flask server for Tradebox API."""

import sys
import datetime

from flask import Flask

import config
import log
import tradeapi

app = Flask(__name__)


@app.route("/")
def index() -> str:
    return "tradebox"


@app.route("/orders/execute/<order_id>", methods=["POST", "GET"])
def execute_order(order_id: int) -> str:
    msg = f"tradebox.py: execute_order(): executing order_id {order_id}"
    log.append(msg)

    tradeapi.execute_order(order_id)
    return str(order_id)


@app.route("/pythonversion")
def python_version() -> str:
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    python_version = sys.version
    return f"{now} <br/><br/> {python_version}"


if __name__ == "__main__":
    if config.ENVIRONMENT == "production":
        # Nginx/gunicorn (or other WSGI server) can use a socket file
        # (e.g. tradebox/tradebox.socket)
        # for WSGI interface.
        # See README.me for a link to setup instructions.
        app.run(host="0.0.0.0")
    elif config.ENVIRONMENT == "development":
        # Port 5555 to avoid conflict with MacOS port 5000.
        # Flask default is 5000.
        app.run(host="127.0.0.1", port=5555, debug=True)
    else:
        msg = "Error: config.ENVIRONMENT is not set or has an invalid value. Please define ENVIRONMENT='production' or ENVIRONMENT='development' in config.py."
        log.append(msg)