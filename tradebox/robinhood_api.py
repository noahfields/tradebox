import robin_stocks.robinhood as r

import config
import database

def login():
    r.login(config.ROBINHOOD_USERNAME, config.ROBINHOOD_PASSWORD)

def update_open_option_positions():
    open_option_positions = r.get_open_option_positions()

    database.set_table_field("open_option_positions", "still_alive", 0)

    for position in open_option_positions:
        last_update_epoch_time = time.time()
        position["last_update_epoch_time"] = last_update_epoch_time
        database.update_open_option_position(position["id"], position)

    database.delete_rows_from_table_by_value("open_option_positions", "still_alive", 0)
    return True

def update_open_option_positions_market_data():
    option_ids = database.get_json_field_from_table_as_list("open_option_positions", "json_data", "option_id")

    database.set_table_field("open_option_positions_market_data", "still_alive", 0)

    for option_id in option_ids:
        option_market_data = r.get_option_market_data_by_id(option_id)
        database.update_open_option_positions_market_data(option_id, option_market_data)

    database.delete_rows_from_table_by_value("open_option_positions_market_data", "still_alive", 0)
    return True

