"""Flask server for Tradebox."""
import sys
import datetime

from flask import Flask

import config
import log
import tradeapi

app = Flask(__name__)


@app.route('/')
def hello() -> str:
    return 'tradebox'


@app.route('/orders/execute/<order_id>', methods=['POST', 'GET'])
def execute_order(order_id: int) -> str:
    log.append(f'tradebox.py: execute_order(): executing order_id {order_id}')
    tradeapi.execute_order(order_id)
    return str(order_id)


@app.route('/console')
def console() -> str:
    return 'console'


@app.route('/pythonversion')
def python_version() -> str:
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    python_version = sys.version
    return f'{now} <br/><br/> {python_version}'


if __name__ == '__main__':
    if config.ENVIRONMENT == 'production':
        app.run(host='0.0.0.0')
    elif config.ENVIRONMENT == 'development':
        app.run(host='0.0.0.0', port=5555, debug=True)
    else:
        msg = 'config.ENVIRONMENT is not set or has an invalid value.\n' \
            + 'Please define ENVIRONMENT=\'production\' or ENVIRONMENT=\'development\' ' \
            + ' in config.py. \n Defaulting to production mode.'
        log.append(msg)
        app.run(host='0.0.0.0')
