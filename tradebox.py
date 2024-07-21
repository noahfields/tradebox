"""Flask server for Tradebox API."""

import datetime
import sys

from flask import Flask

import config
import log
import tradeapi

app = Flask(__name__)


@app.route('/')
def index() -> str:
    return 'tradebox'


@app.route('/orders/execute/<order_id>', methods=['POST', 'GET'])
def execute_order(order_id: int) -> str:
    msg = f'tradebox.py: execute_order(): executing order_id {order_id}'
    log.append(msg)

    tradeapi.execute_order(order_id)
    return str(order_id)


@app.route('/pythonversion')
def python_version() -> str:
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    python_version = sys.version
    return f'{now} <br/><br/> {python_version}'


if __name__ == '__main__':
    # This section runs a local development server.
    # Do not use in production.
    #
    # Running 'python tradebox.py' will run a local development server: 
    # IP Address, Port, and Debug settings in config.py.
    #
    # Alternatively, you can start the development server
    # with 'flask --app tradebox run'
    # on 127.0.0.1:5000.
    #
    # When running the Flask application in production
    # via gunicorn or other wsgi server
    # this section is not run and config.py has 
    # no effect on server settings.
    app.run(host=config.DEV_IP, 
            port=config.DEV_PORT, 
            debug=config.DEV_DEBUG
        )