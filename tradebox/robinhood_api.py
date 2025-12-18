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
    # Set market_data still_alive so it gets deleted if no longer alive in an order
    database.set_table_field("open_broker_option_orders_market_data", "still_alive", 0)
    logger.info("open_broker_option_orders_market_data still_alive set to 0")

    open_broker_option_order_legs = database.get_json_field_from_table("open_broker_option_orders", "json_data", "legs")
    # SAMPLE DATA open_broker_option_order_legs 
    # [('[{"executions":[],"id":"69443130-4608-43c0-8ce5-1f225c685044","option":"https://api.robinhood.com/options/instruments/4aed1bc4-f8d4-48a7-a5b9-288ee30c63be/","position_effect":"close","ratio_quantity":1,"side":"sell","expiration_date":"2025-12-19","strike_price":"34.0000","option_type":"put","long_strategy_code":"4aed1bc4-f8d4-48a7-a5b9-288ee30c63be_L1","short_strategy_code":"4aed1bc4-f8d4-48a7-a5b9-288ee30c63be_S1"}]',)]
    logger.info(f"Fetched open_broker_option_orders: {open_broker_option_order_legs}")

    cleaned_option_leg_ids = []
    for leg in open_broker_option_order_legs:
        # SAMPLE DATA order
        #('[{"executions":[],"id":"69443130-4608-43c0-8ce5-1f225c685044","option":"https://api.robinhood.com/options/instruments/4aed1bc4-f8d4-48a7-a5b9-288ee30c63be/","position_effect":"close","ratio_quantity":1,"side":"sell","expiration_date":"2025-12-19","strike_price":"34.0000","option_type":"put","long_strategy_code":"4aed1bc4-f8d4-48a7-a5b9-288ee30c63be_L1","short_strategy_code":"4aed1bc4-f8d4-48a7-a5b9-288ee30c63be_S1"}]',)
        logger.info(f"leg ready for json cleaning: {leg}")

        leg = json.loads(leg[0])
        # SAMPLE DATA order_list
        # [{'executions': [], 'id': '69443130-4608-43c0-8ce5-1f225c685044', 'option': 'https://api.robinhood.com/options/instruments/4aed1bc4-f8d4-48a7-a5b9-288ee30c63be/', 'position_effect': 'close', 'ratio_quantity': 1, 'side': 'sell', 'expiration_date': '2025-12-19', 'strike_price': '34.0000', 'option_type': 'put', 'long_strategy_code': '4aed1bc4-f8d4-48a7-a5b9-288ee30c63be_L1', 'short_strategy_code': '4aed1bc4-f8d4-48a7-a5b9-288ee30c63be_S1'}]
        leg = leg[0]
        logger.info(f"Leg after json cleaning: {leg}")

        market_option_id = leg["option"].split("/")[5]
        cleaned_option_leg_ids.append(market_option_id)
        logger.info(f"Cleaned option IDs: {cleaned_option_leg_ids}")

    for option_id in cleaned_option_leg_ids:
        option_market_data = r.get_option_market_data_by_id(option_id)
        # SAMPLE DATA option_market_data
        # [{'adjusted_mark_price': '0.030000', 'adjusted_mark_price_round_down': '0.030000', 'ask_price': '0.040000', 'ask_size': 2231, 'bid_price': '0.020000', 'bid_size': 303, 'break_even_price': '33.970000', 'high_price': '0.070000', 'instrument': 'https://api.robinhood.com/options/instruments/4aed1bc4-f8d4-48a7-a5b9-288ee30c63be/', 'instrument_id': '4aed1bc4-f8d4-48a7-a5b9-288ee30c63be', 'last_trade_price': '0.030000', 'last_trade_size': 1, 'low_price': '0.010000', 'mark_price': '0.030000', 'open_interest': 13917, 'previous_close_date': '2025-12-17', 'previous_close_price': '0.090000', 'updated_at': '2025-12-18T17:48:33.094328622Z', 'volume': 551, 'symbol': 'INTC', 'occ_symbol': 'INTC  251219P00034000', 'state': 'active', 'chance_of_profit_long': '0.050390', 'chance_of_profit_short': '0.949610', 'delta': '-0.048504', 'gamma': '0.068714', 'implied_volatility': '0.723973', 'rho': '-0.000056', 'theta': '-0.064891', 'vega': '0.002037', 'pricing_model': 'Bjerksund-Stensland 1993', 'high_fill_rate_buy_price': '0.035000', 'high_fill_rate_sell_price': '0.024000', 'low_fill_rate_buy_price': '0.026000', 'low_fill_rate_sell_price': '0.033000'}]
        logger.info(f"Leg option data for {option_id}: {option_market_data}")

        json_data_string = json.dumps(option_market_data[0])
        logger.info(f"Json string for option_market_data: {json_data_string}")
        last_update_epoch_time = time.time()

        database.update_open_broker_option_orders_market_data(option_id, json_data_string, last_update_epoch_time, still_alive=1)

    database.delete_rows_from_table_by_value("open_broker_option_orders_market_data", "still_alive", 0)
    return True