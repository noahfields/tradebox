"""Flask server for Tradebox API."""

import datetime
import sys
import traceback

from flask import Flask

import config
import log
import tradeapi

app = Flask(__name__)


def log_traceback(ex):
    tb_lines = traceback.format_exception(ex.__class__, ex, ex.__traceback__)
    tb_text = ''.join(tb_lines)
    log.append(tb_text)


@app.route('/')
def index() -> str:
    current_datetime_string = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    python_version = sys.version

    html = 'Welcome to Tradebox. <br />' \
         + f'Current date and time: {current_datetime_string} <br />' \
         + f'Python version: {python_version}'
    return html


@app.route('/orders/execute/<order_id>', methods=['POST', 'GET'])
def execute_order(order_id: int) -> str:
    try:
        msg = f'tradebox.py: execute_order(): executing order_id {order_id}. \n' \
            + f'Entering tradeapi.execute_order({order_id}).'
        log.append(msg)

        tradeapi.execute_order(order_id)

        html = f'Executed order #{order_id}.'
        return html
    except Exception as ex:
        log_traceback(ex)
        html = f'There was an issue executing order #{order_id}. Writing traceback to log file.'
        return html


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