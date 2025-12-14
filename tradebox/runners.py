import sys
import time

import database
import robinhood_api
import log

def runner_update_open_option_positions():
    success = robinhood_api.update_open_option_positions()
    return success

def runner_update_open_option_positions_market_data():
    robinhood_api.update_open_option_positions_market_data()

def runner_update_broker_option_orders():
    return True

def runner_update_broker_option_orders_market_data():
    return True

def runner_update_trigger_options_orders_market_data():
    return True

def is_runner_name(runner_name):
    runner_names = [
        "runner_update_open_option_positions", 
        "runner_update_option_positions_market_data", 
        "runner_update_broker_option_orders"
    ]
    if runner_name in runner_names:
        return True
    else:
        return False

def is_runner_active(runner_name):
    return True

# arguments: runner_function_name(argv[1]), refresh interval in seconds (argv[2])
if __name__ == "__main__":
    database.create_database_tables()

    runner_name = sys.argv[1]
    if is_runner_name(runner_name):
        log.log(f"runners.py: Valid runner name: {runner_name}")
    else:
        log.log(f"runners.py: Invalid runner name: {runner_name}")
        sys.exit()
        
    refresh_interval_in_seconds = int(sys.argv[2])
    if not isinstance(refresh_interval_in_seconds, int):
        log.log(f"runners.py: Invalid refresh_interval_in_seconds: {refresh_interval_in_seconds}")
        sys.exit()
    
    while is_runner_active(runner_name):
        eval(f"{runner_name}()")
        time.sleep(refresh_interval_in_seconds)


        

    
