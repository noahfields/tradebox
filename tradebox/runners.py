from concurrent.futures import ThreadPoolExecutor
import logging
import os
import sys
import time

import config
import database
import robinhood_api

runners = { "runner_update_open_option_positions": 7,
            "runner_update_open_option_positions_market_data": 7,
            "runner_update_broker_option_orders": 15,
            "runner_update_broker_option_orders_market_data": 7,
            "runner_update_trigger_option_orders_market_data": 7,
        }

def runner_update_open_option_positions():
    print('updating open option positions')
    robinhood_api.update_open_option_positions()

def runner_update_open_option_positions_market_data():
    return True
    robinhood_api.update_open_option_positions_market_data()

def runner_update_broker_option_orders():
    return True

def runner_update_broker_option_orders_market_data():
    return True

def runner_update_trigger_option_orders_market_data():
    return True

def get_runner_functions():
    return [
        name for name, obj in globals().items()
        if name.startswith("runner_") and callable(obj)
    ]

def is_runner_name(runner_name):
    runner_funcs = get_runner_functions()
    return runner_name in runner_funcs

def is_runner_active(runner_name):
    return True

def run_runner(runner_function_name):
    while True:
        runner_info = database.get_runner_info(runner_function_name)
        eval(runner_function_name + "()")
        time.sleep(runner_info["interval"])

# arguments: runner_function_name(argv[1]), refresh interval in seconds (argv[2])
if __name__ == "__main__":
    robinhood_api.login()
    database.drop_runners_table()
    database.create_database_tables()
    database.populate_runners_table(runners)

    max_workers = min(len(get_runner_functions()) * 2)
    with ThreadPoolExecutor(max_workers=max_workers) as runner_threads:
        for runner_function_name in get_runner_functions():
            runner_threads.submit(run_runner, runner_function_name)


        

    
