import json
import time

import robin_stocks.robinhood as r

import config
import database
import log

# Logging
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
        log.error(f"Error updating open option positions: {e}")
        return False

def update_open_option_positions_market_data():
    logger.debug("Starting update_option_positions_market_data")
    option_ids = database.get_json_field_from_table_as_list("open_option_positions", "json_data", "option_id")
    logger.debug(f"option_ids: {option_ids}")

    database.set_table_field("open_option_positions_market_data", "still_alive", 0)

    for option_id in option_ids:
        option_market_data = r.get_option_market_data_by_id(option_id)
        database.update_open_option_positions_market_data(option_id, option_market_data)

    database.delete_rows_from_table_by_value("open_option_positions_market_data", "still_alive", 0)
    return True

def update_open_broker_option_broker_orders():
    try:
        open_option_orders = r.get_all_open_option_orders()

        database.set_table_field("open_broker_option_orders", "still_alive", 0)

        for position in open_option_positions:
            still_alive = 1
            epoch_time = time.time()
            json_data = json.dumps(position)
            database.update_open_option_position(position["id"], json_data, still_alive, epoch_time)

        database.delete_rows_from_table_by_value("open_option_positions", "still_alive", 0)
        return True
    except Exception as e:
        print(f"Error updating open option positions: {e}")
        return False