import json
import logging
import time

import robin_stocks.robinhood as r

import config
import database

# Logging
logger = None

API_VERIFICATION_DEFAULT_KEYSETS = {
	"get_open_option_positions": {'account': 'https://api.robinhood.com/accounts/5QU45833/', 'account_number': '5QU45833', 'average_price': '-16.0000', 'chain_id': '72362eb7-bc7c-4d10-9be4-48a53fffd101', 'chain_symbol': 'IWM', 'id': '876c8360-ce18-4c31-b31f-e760270b091d', 'option': 'https://api.robinhood.com/options/instruments/2b4dde4d-c7b7-4c6c-8290-a70f76cedaf9/', 'type': 'short', 'pending_buy_quantity': '0.0000', 'pending_expired_quantity': '0.0000', 'pending_expiration_quantity': '0.0000', 'pending_exercise_quantity': '0.0000', 'pending_assignment_quantity': '0.0000', 'pending_sell_quantity': '0.0000', 'quantity': '17.0000', 'intraday_quantity': '17.0000', 'intraday_average_open_price': '-16.0000', 'created_at': '2025-12-19T21:09:50.112600Z', 'expiration_date': '2025-12-22', 'trade_value_multiplier': '100.0000', 'updated_at': '2025-12-19T21:09:50.501378Z', 'url': 'https://api.robinhood.com/options/positions/876c8360-ce18-4c31-b31f-e760270b091d/', 'option_id': '2b4dde4d-c7b7-4c6c-8290-a70f76cedaf9', 'clearing_running_quantity': '17.0000', 'clearing_cost_basis': '272.0000', 'clearing_direction': 'credit', 'clearing_intraday_running_quantity': '17.0000', 'clearing_intraday_cost_basis': '272.0000', 'clearing_intraday_direction': 'credit', 'opened_at': '2025-12-19T21:09:50.116471Z'},

	"get_option_market_data_by_id": {'adjusted_mark_price': '0.200000', 'adjusted_mark_price_round_down': '0.200000', 'ask_price': '0.210000', 'ask_size': 2, 'bid_price': '0.190000', 'bid_size': 98, 'break_even_price': '248.800000', 'high_price': '1.330000', 'instrument': 'https://api.robinhood.com/options/instruments/2b4dde4d-c7b7-4c6c-8290-a70f76cedaf9/', 'instrument_id': '2b4dde4d-c7b7-4c6c-8290-a70f76cedaf9', 'last_trade_price': '0.210000', 'last_trade_size': 1, 'low_price': '0.160000', 'mark_price': '0.200000', 'open_interest': 1473, 'previous_close_date': '2025-12-18', 'previous_close_price': '1.810000', 'updated_at': '2025-12-19T21:14:59.805486725Z', 'volume': 9984, 'symbol': 'IWM', 'occ_symbol': 'IWM   251222P00249000', 'state': 'active', 'chance_of_profit_long': '0.159818', 'chance_of_profit_short': '0.840182', 'delta': '-0.183593', 'gamma': '0.133426', 'implied_volatility': '0.117049', 'rho': '-0.002116', 'theta': '-0.152646', 'vega': '0.045217', 'pricing_model': 'Bjerksund-Stensland 1993', 'high_fill_rate_buy_price': '0.205000', 'high_fill_rate_sell_price': '0.194000', 'low_fill_rate_buy_price': '0.195000', 'low_fill_rate_sell_price': '0.204000'},

	"get_all_open_option_orders": {'account_number': '5QU45833', 'cancel_url': 'https://api.robinhood.com/options/orders/694781e4-11ef-4af7-b3cc-a739ccec0da3/cancel/', 'canceled_quantity': '0.00000', 'created_at': '2025-12-21T05:13:08.046546Z', 'direction': 'debit', 'id': '694781e4-11ef-4af7-b3cc-a739ccec0da3', 'legs': [{'executions': [], 'id': '694781e4-0f2f-4fee-bc09-97f3c2c8c0d9', 'option': 'https://api.robinhood.com/options/instruments/4e188c22-aef8-4f43-8dd0-411acc486654/', 'position_effect': 'open', 'ratio_quantity': 1, 'side': 'buy', 'expiration_date': '2025-12-23', 'strike_price': '255.0000', 'option_type': 'call', 'long_strategy_code': '4e188c22-aef8-4f43-8dd0-411acc486654_L1', 'short_strategy_code': '4e188c22-aef8-4f43-8dd0-411acc486654_S1'}], 'pending_quantity': '2.00000', 'premium': '3.00000000', 'processed_premium': '0', 'processed_premium_direction': 'debit', 'market_hours': 'regular_hours', 'net_amount': '0', 'net_amount_direction': 'debit', 'price': '0.03000000', 'processed_quantity': '0.00000', 'quantity': '2.00000', 'ref_id': 'dd0c09ef-716c-4261-953d-62a7259fbea8', 'regulatory_fees': '0', 'contract_fees': '0', 'gold_savings': '0', 'state': 'queued', 'time_in_force': 'gfd', 'trigger': 'immediate', 'type': 'limit', 'updated_at': '2025-12-21T05:13:08.384132Z', 'chain_id': '72362eb7-bc7c-4d10-9be4-48a53fffd101', 'chain_symbol': 'IWM', 'response_category': None, 'opening_strategy': 'long_call', 'closing_strategy': None, 'stop_price': None, 'form_source': 'option_chain', 'client_bid_at_submission': '0.11000000', 'client_ask_at_submission': '0.13000000', 'client_time_at_submission': None, 'average_net_premium_paid': '0.00000000', 'estimated_total_net_amount': '6.04', 'estimated_total_net_amount_direction': 'debit', 'is_replaceable': True, 'strategy': 'long_call', 'derived_state': 'queued', 'sales_taxes': []},
}

def verify_api_key_match(api_verification_key_name: str, live_data_dict: dict) -> bool:
	default_data_dict = API_VERIFICATION_DEFAULT_KEYSETS[api_verification_key_name]

	default_keys_match_live_keys = verify_dict_keys_match(default_data_dict, live_data_dict)

	if not default_keys_match_live_keys:
		logger.critical(
			"API KEY VERIFICATION FAILURE\n"
			"Default keys do not match live keys.\n"
			"Runner may fail due to an update to Robinhood API data.\n"
			f"Check robinhood_api {api_verification_key_name} for rewrite."
		)
		keys_only_in_default_data_dict = get_unique_keys_in_first_dict(
			default_data_dict, 
			live_data_dict
		)
		keys_only_in_live_data_dict = get_unique_keys_in_first_dict(
			live_data_dict,
			default_data_dict
		)
		logger.critical(
			f"Keys only in DEFAULT {api_verification_key_name} row:\n"
			f"{keys_only_in_default_data_dict}"
		)
		logger.critical(
			f"Keys only in LIVE {api_verification_key_name} row:\n"
			f"{keys_only_in_live_data_dict}"
		)
		return False
	else:
		logger.info(
			f"Robinhood API keys for {api_verification_key_name} match."
		)
		return True

def verify_dict_keys_match(dict1: dict, dict2: dict) -> bool:
	return dict1.keys() == dict2.keys()

def get_unique_keys_in_first_dict(default_dict: dict, other_dict: dict) -> set[str]:
	keys_only_in_first_dict = set(default_dict) - set(other_dict)
	return keys_only_in_first_dict

def login() -> bool:
	try:
		res = r.login(config.ROBINHOOD_USERNAME, config.ROBINHOOD_PASSWORD)
		logger.debug(f"Logged into Robinhood successfully: {res}")
		return True
	except Exception as e:
		logger.critical(f"Issue logging into Robinhood: {e}")
		return False


def update_open_option_positions():
	try:
		open_option_positions = r.get_open_option_positions()
		logger.info(f"Robinhood API get_open_option_positions() raw result: {open_option_positions}")

		if len(open_option_positions) > 0:
			verify_api_key_match(
				"get_open_option_positions", 
				open_option_positions[0]
			)

		database.set_table_field("open_option_positions", "still_alive", 0)

		for position in open_option_positions:
			json_data = json.dumps(position)
			last_update_epoch_time = time.time()
			still_alive = 1
			database.update_open_option_position(
				position["id"], json_data, last_update_epoch_time, still_alive
			)

		database.delete_rows_from_table_by_value(
			"open_option_positions", "still_alive", 0
		)
		logger.debug("Successfully updated open_option_positions.")
		return True
	except Exception as e:
		logger.critical(f"Error updating open_option_positions: {e}")
		return False


def update_open_option_positions_market_data():
	try:
		option_ids = database.get_json_field_from_table_as_list(
			"open_option_positions", "json_data", "option_id"
		)

		cleaned_option_ids = []
		for option_tuple in option_ids:
			cleaned_option_ids.append(option_tuple)

		database.set_table_field(
			"open_option_positions_market_data", "still_alive", 0
		)

		for option_id in cleaned_option_ids:
			option_market_data = r.get_option_market_data_by_id(option_id)[0]
			logger.info(
				f"update_open_option_positions_market_data sample API data:\n"
				f"{option_market_data}"
			)

			verify_api_key_match("get_option_market_data_by_id", option_market_data)

			json_data = json.dumps(option_market_data)
			last_update_epoch_time = time.time()
			still_alive = 1
			database.update_open_option_positions_market_data(
				option_id, json_data, last_update_epoch_time, still_alive
			)

		database.delete_rows_from_table_by_value(
			"open_option_positions_market_data", "still_alive", 0
		)
		return True
	except Exception as e:
		logger.error(f"Error updating open_option_positions_market_data: {e}")
		return False


def update_open_broker_option_orders():
	try:
		open_option_orders = r.get_all_open_option_orders()
	except Exception as e:
		logger.critical(
			"Robinhood API Error: 'get_open_option_orders'\n"
			f"Exception information: {e}"
		)
		return False

	logger.info(
		"Robinhood API data resut for get_all_open_option_orders():\n"
		f"{open_option_orders}"
	)

	database.set_table_field("open_broker_option_orders", "still_alive", 0)

	for order in open_option_orders:
		logger.info(
			"API info for order in update_open_broker_option_orders:\n"
			f"{order}"
		)

		verify_api_key_match("get_all_open_option_orders", order)

		order_id = order["id"]
		json_data = json.dumps(order)
		still_alive = 1
		last_update_epoch_time = time.time()
		database.update_open_broker_option_order(
			order_id, json_data, last_update_epoch_time, still_alive
		)


	database.delete_rows_from_table_by_value(
		"open_broker_option_orders", "still_alive", 0
	)
	return True


def update_open_broker_option_orders_market_data():
	database.set_table_field(
		"open_broker_option_orders_market_data", "still_alive", 0
	)

	open_broker_option_order_legs = database.get_json_field_from_table(
		"open_broker_option_orders", "json_data", "legs"
	)
	# SAMPLE DATA open_broker_option_order_legs
	# [('[{"executions":[],"id":"69443130-4608-43c0-8ce5-1f225c685044","option":"https://api.robinhood.com/options/instruments/4aed1bc4-f8d4-48a7-a5b9-288ee30c63be/","position_effect":"close","ratio_quantity":1,"side":"sell","expiration_date":"2025-12-19","strike_price":"34.0000","option_type":"put","long_strategy_code":"4aed1bc4-f8d4-48a7-a5b9-288ee30c63be_L1","short_strategy_code":"4aed1bc4-f8d4-48a7-a5b9-288ee30c63be_S1"}]',)]
	logger.info(
		f"Fetched open_broker_option_orders legs: {open_broker_option_order_legs}"
	)

	cleaned_option_leg_ids = []
	for leg in open_broker_option_order_legs:
		# SAMPLE DATA leg
		# ('[{"executions":[],"id":"69443130-4608-43c0-8ce5-1f225c685044","option":"https://api.robinhood.com/options/instruments/4aed1bc4-f8d4-48a7-a5b9-288ee30c63be/","position_effect":"close","ratio_quantity":1,"side":"sell","expiration_date":"2025-12-19","strike_price":"34.0000","option_type":"put","long_strategy_code":"4aed1bc4-f8d4-48a7-a5b9-288ee30c63be_L1","short_strategy_code":"4aed1bc4-f8d4-48a7-a5b9-288ee30c63be_S1"}]',)
		logger.info(f"leg ready for json cleaning: {leg}")

		leg = json.loads(leg[0])
		# SAMPLE DATA leg
		# [{'executions': [], 'id': '69443130-4608-43c0-8ce5-1f225c685044', 'option': 'https://api.robinhood.com/options/instruments/4aed1bc4-f8d4-48a7-a5b9-288ee30c63be/', 'position_effect': 'close', 'ratio_quantity': 1, 'side': 'sell', 'expiration_date': '2025-12-19', 'strike_price': '34.0000', 'option_type': 'put', 'long_strategy_code': '4aed1bc4-f8d4-48a7-a5b9-288ee30c63be_L1', 'short_strategy_code': '4aed1bc4-f8d4-48a7-a5b9-288ee30c63be_S1'}]
		leg = leg[0]
		logger.info(f"Leg after json cleaning: {leg}")

		market_option_id = leg["option"].split("/")[5]
		cleaned_option_leg_ids.append(market_option_id)
		logger.info(f"Cleaned option IDs: {cleaned_option_leg_ids}")

	for option_id in cleaned_option_leg_ids:
		option_market_data = r.get_option_market_data_by_id(option_id)
		option_market_data = option_market_data[0]
		logger.info(
			"API option_market_data_by_id in update_open_broker_option_orders_market_data:\n"
			f"{option_market_data}"
		)

		verify_api_key_match("get_option_market_data_by_id", option_market_data)

		logger.info(f"Leg option market data for {option_id}: {option_market_data}")

		json_data = json.dumps(option_market_data)
		last_update_epoch_time = time.time()
		still_alive = 1
		database.update_open_broker_option_orders_market_data(
			option_id, json_data, last_update_epoch_time, still_alive
		)

	database.delete_rows_from_table_by_value(
		"open_broker_option_orders_market_data", "still_alive", 0
	)
	return True