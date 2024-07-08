import sys
import datetime

from flask import Flask

import config
import log
import tradeapi

app = Flask(__name__)


@app.route('/')
def hello():
    return 'tradebox'


@app.route('/orders/execute/<order_id>', methods=['POST', 'GET'])
def execute_order(order_id):
    log.append(f'TRADEBOX flask: executing order_id {order_id}')
    tradeapi.execute_order(order_id)
    return str(order_id)


@app.route('/console')
def console():
    return 'console'


@app.route('/pythonversion')
def python_version():
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    python_version = sys.version
    return f'{now} <br/><br/> {python_version}'


if __name__ == '__main__':
    if config.ENVIRONMENT == 'production':
        app.run(host='0.0.0.0')
    elif config.ENVIRONMENT == 'development':
        app.run(host='0.0.0.0', port=5555, debug=True)
    else:
        msg = 'config.ENVIRONMENT is not set or has an invalid value. \nPlease define ENVIRONMENT=\'production\' or ENVIRONMENT=\'development\' in config.py. \n Defaulting to production mode.'
        print(msg)
        log.append(msg)
        app.run(host='0.0.0.0')
