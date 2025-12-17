import json
import time

import robin_stocks.robinhood as r

import config
import database
import log

# Logging
logger = log.get_logger(log_title="robinhood_api")

def login() -> bool:
    try:
        res = r.login(config.ROBINHOOD_USERNAME, config.ROBINHOOD_PASSWORD)
        logger.info(f"Logged into Robinhood successfully: {res}")
        return True
    except Exception as e:
        logger.warning(f"Issue logging into Robinhood: {e}")
        return False

def update_open_option_positions():
    try:
        open_option_positions = r.get_open_option_positions()

        database.set_table_field("open_option_positions", "still_alive", 0)

        for position in open_option_positions:
            still_alive = 1
            epoch_time = time.time()
            json_data = json.dumps(position)
            database.update_open_option_position(position["id"], json_data, still_alive, epoch_time)

        database.delete_rows_from_table_by_value("open_option_positions", "still_alive", 0)
        return True
    except Exception as e:
        log.error(f"Error updating open_option_positions: {e}")
        return False

def update_open_option_positions_market_data():
    try:
        option_ids = database.get_json_field_from_table_as_list("open_option_positions", "json_data", "option_id")

        cleaned_option_ids = []
        for option_tuple in option_ids:
            cleaned_option_ids.append(option_tuple)

        database.set_table_field("open_option_positions_market_data", "still_alive", 0)

        for option_id in cleaned_option_ids:
            option_market_data = r.get_option_market_data_by_id(option_id)
            database.update_open_option_positions_market_data(option_id, 1, option_market_data, time.time())

        database.delete_rows_from_table_by_value("open_option_positions_market_data", "still_alive", 0)
        return True
    except Exception as e:
        log.error(f"Error updating open_option_positions_market_data: {e}")
        return False

def update_open_broker_option_orders():
    try:
        open_option_orders = r.get_all_open_option_orders()

        database.set_table_field("open_broker_option_orders", "still_alive", 0)

        for order in open_option_orders:
            order_id = order["id"]
            json_data = json.dumps(order)
            still_alive = 1
            last_update_epoch_time = time.time()
            database.update_open_broker_option_order(order_id, json_data, still_alive, last_update_epoch_time)

        database.delete_rows_from_table_by_value("open_broker_option_orders", "still_alive", 0)
        return True
    except Exception as e:
        logger.critical(f"Critical error updating open_broker_option_orders: {e}")
        return False
    
def update_open_broker_option_orders_market_data():
    orders = database.get_json_field_from_table("open_broker_option_orders", "json_data", "legs")
    print('order legs')
    print(orders)

    [('[{"executions":[],"id":"69432299-8063-4347-8d3b-f4d5c097c9af","option":"https://api.robinhood.com/options/instruments/4aed1bc4-f8d4-48a7-a5b9-288ee30c63be/","position_effect":"close","ratio_quantity":1,"side":"sell","expiration_date":"2025-12-19","strike_price":"34.0000","option_type":"put","long_strategy_code":"4aed1bc4-f8d4-48a7-a5b9-288ee30c63be_L1","short_strategy_code":"4aed1bc4-f8d4-48a7-a5b9-288ee30c63be_S1"}]',), ('[{"executions":[],"id":"69431cf6-c2f9-40d2-9728-4701e9a42777","option":"https://api.robinhood.com/options/instruments/4aed1bc4-f8d4-48a7-a5b9-288ee30c63be/","position_effect":"close","ratio_quantity":1,"side":"sell","expiration_date":"2025-12-19","strike_price":"34.0000","option_type":"put","long_strategy_code":"4aed1bc4-f8d4-48a7-a5b9-288ee30c63be_L1","short_strategy_code":"4aed1bc4-f8d4-48a7-a5b9-288ee30c63be_S1"}]',)]

    # cleaned_option_ids = []
    # for option_tuple in option_ids:
    #     cleaned_option_ids.append(option_tuple)

    # database.set_table_field("open_option_positions_market_data", "still_alive", 0)

    # for option_id in cleaned_option_ids:
    #     option_market_data = r.get_option_market_data_by_id(option_id)
    #     database.update_open_option_positions_market_data(option_id, 1, option_market_data, time.time())

    # database.delete_rows_from_table_by_value("open_option_positions_market_data", "still_alive", 0)
    # return True