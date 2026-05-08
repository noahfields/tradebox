"""Flask server for Tradebox API."""

import datetime
import json
import sys
import subprocess

from flask import Flask, render_template
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

import config
import database
import robinhood_wrappers
import systemd
#import tradeapi

app = Flask(__name__)
auth = HTTPBasicAuth()

users = {
    "nfields2": generate_password_hash("2password2"),
}


@auth.verify_password
def verify_password(username, password):
    if username in users and \
            check_password_hash(users.get(username), password):
        return username

@app.route('/')
@auth.login_required
def index() -> str:
    return render_template("index.html")

@app.route('/create_all_tables')
@auth.login_required
def create_all_tables() -> str:
    database.create_all_tables()
    return('1')

@app.route('/drop_all_tables')
@auth.login_required
def drop_all_tables() -> str:
    database.drop_all_tables()
    return('1')

@app.route('/install_runners')
@auth.login_required
def install_runners():
    systemd.install_systemd_services()
    return('1')


@app.route('/remove_runners')
@auth.login_required
def remove_runners():
    systemd.remove_systemd_services()
    return('1')

@app.route('/enable_runners')
@auth.login_required
def enable_runners():
    systemd.enable_systemd_services()
    return('1')

@app.route('/disable_runners')
@auth.login_required
def disable_runners():
    systemd.disable_systemd_services()
    return('1')

@app.route('/start_runners')
@auth.login_required
def start_runners():
    systemd.start_systemd_services()
    return('1')

@app.route('/stop_runners')
def stop_runners():
    systemd.stop_systemd_services()
    return('1')

@app.route('/rh_login')
@auth.login_required
def rh_login():
    robinhood_wrappers.login()
    return('1')

@app.route('/rh_logout')
@auth.login_required
def rh_logout():
    robinhood_wrappers.logout_and_remove_token()
    return('1')

@app.route('/restart_server')
@auth.login_required
def restart_server():
    subprocess.run(f"/usr/bin/sudo reboot", shell=True, check=True)
    return('1')

@app.route('/portfolio_profile')
@auth.login_required
def portfolio_profile():
    return(database.get_json_portfolio_profile())

@app.route('/get_all_runners_status')
@auth.login_required
def get_all_runners_status():
    return(database.get_all_runners_status(return_json=True))

# @app.route('/get_open_option_positions')
# @auth.login_required
# def get_open_option_positions():
#     return(database.get_open_option_positions(return_json=True))

# @app.route('/get_open_option_position_market_data_by_id/<option_id>')
# @auth.login_required
# def get_open_option_position_market_data(option_id):
#     res = database.get_rows_from_table_select_by_json_field_value(
#         'open_option_positions_market_data', 
#         'json_data',
#         'instrument_id',
#         option_id,
#         return_json=False)
#     print("market data")
#     print(res)
#     return json.dumps(res[0][1])
    
# @app.route('/get_open_option_position_instrument_data_by_id/<option_id>')
# @auth.login_required
# def get_open_option_position_instrument_data(option_id):
#     res = database.get_rows_from_table_select_by_json_field_value(
#         'open_option_positions_instrument_data', 
#         'json_data',
#         'id',
#         option_id,
#         return_json=False)
#     print("instrument data")
#     print(res)
#     return json.dumps(res[0][1])

@app.route('/get_mini_position_info')
@auth.login_required
def get_mini_position_info():
    res = database.get_mini_position_info(return_json=True)
    return res


# @app.route('/')
# def index() -> str:
#     current_datetime_string = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
#     python_version = sys.version

#     html = 'Welcome to Tradebox. <br />' \
#          + f'Current date and time: {current_datetime_string} <br />' \
#          + f'Python version: {python_version}'
#     return html


# @app.route('/orders/execute/<order_id>', methods=['POST', 'GET'])
# def execute_order(order_id: int) -> str:
#     try:
#         order_id = int(order_id)
#     except ValueError:
#         pass

#     try:
#         msg = f'tradebox.py: execute_order(): executing order_id {order_id}. \n' \
#             + f'Entering tradeapi.execute_order({order_id}).'
#         log.append(msg)

#         tradeapi.execute_order(order_id)

#         html = f'Executed order #{order_id}.'
#         return html
#     except Exception as ex:
#         pass


if __name__ == '__main__':
    app.run(
            host=config.DEVELOPMENT_FLASK_IP, 
            port=int(config.DEVELOPMENT_FLASK_PORT),
            debug=bool(config.DEVELOPMENT_FLASK_DEBUG)
    )


