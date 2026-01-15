from concurrent.futures import ThreadPoolExecutor
import json
import logging
import time
import uuid

import robin_stocks.robinhood as r

import config
import database
import log
import orders
import schema

logger = log.setup_runners_logger("runners")


class MonitorRunner:
	def __init__(self, runner_dict):
		self.monitor_function = runner_dict["monitor_function"]

		self.status = {
			"runner_name_pk": runner_dict["runner_name"],
			"active": runner_dict["active"],
			"adjusted_interval": runner_dict["default_interval"],
			"default_interval": runner_dict["default_interval"],
			"current_update_success": False,
			"previous_update_success": False,
			"epoch_time_previous_success": 0,
		}

		logger.info(
			f"Runner {self.status['runner_name_pk']} initiated.\nRunner object info:\n"
			f"monitor_function: {self.monitor_function}\n"
			f"Runner status:\n{self.status}",
			extra={"runner": self.status["runner_name_pk"]},
		)

	def get_runner_status(self):
		status = database.get_runner_status(self.status["runner_name_pk"])
		logger.info(
			f"Returning fetched runner status: {status}",
			extra={"runner": self.status["runner_name_pk"]},
		)
		return status

	def write_runner_status(self):
		database.write_runner_status(self.status)

class DataFetchRunner:
	def __init__(self, runner_dict):
		self.get_data_function = runner_dict["get_data_function"]
		self.verify_data_keyset = runner_dict["verify_data_keyset"]
		self.store_data_function = runner_dict["store_data_function"]

		self.status = {
			"runner_name_pk": runner_dict["runner_name"],
			"active": runner_dict["active"],
			"adjusted_interval": runner_dict["default_interval"],
			"default_interval": runner_dict["default_interval"],
			"current_update_success": False,
			"previous_update_success": False,
			"epoch_time_previous_success": 0,
		}

		logger.info(
			f"Runner {self.status['runner_name_pk']} initiated.\nRunner object info:\n"
			f"get_data_function: {self.get_data_function}\n"
			f"verify_data_keyset: {self.verify_data_keyset}\n"
			f"store_data_function: {self.store_data_function}\n"
			f"Runner status:\n{self.status}",
			extra={"runner": self.status["runner_name_pk"]},
		)

	def get_data(self):
		api_data = self.get_data_function()
		logger.info(
			f"Received api_data for {self.status['runner_name_pk']}: {api_data}",
			extra={"runner": self.status["runner_name_pk"]},
		)
		return api_data

	def verify_data(self, api_data_row: dict) -> bool:
		match_bool = verify_api_key_match(
			self.verify_data_keyset,
			api_data_row,
			self.status["runner_name_pk"],
		)
		return match_bool

	def store_data(self, api_data) -> None:
		self.store_data_function(api_data)

	def get_runner_status(self):
		status = database.get_runner_status(self.status["runner_name_pk"])
		logger.info(
			f"Returning fetched runner status: {status}",
			extra={"runner": self.status["runner_name_pk"]},
		)
		return status

	def write_runner_status(self):
		database.write_runner_status(self.status)


def verify_api_key_match(
	api_verification_key_name: str,
	live_data_dict: dict,
	runner_name: str = "unknown",
) -> bool:
	default_data_dict = API_VERIFICATION_DEFAULT_KEYSETS[
		api_verification_key_name
	]

	default_keys_match_live_keys = verify_dict_keys_match(
		default_data_dict, live_data_dict
	)

	if not default_keys_match_live_keys:
		logger.critical(
			"API KEY VERIFICATION FAILURE\n"
			"Default keys do not match live keys.\n"
			"Runner may fail due to an update to Robinhood API data.\n"
			f"Check {api_verification_key_name} for rewrite.",
			extra={"runner": runner_name},
		)
		keys_only_in_default_data_dict = get_unique_keys_in_first_dict(
			default_data_dict, live_data_dict
		)
		keys_only_in_live_data_dict = get_unique_keys_in_first_dict(
			live_data_dict, default_data_dict
		)
		logger.critical(
			f"Keys only in DEFAULT {api_verification_key_name} row:\n"
			f"{keys_only_in_default_data_dict}",
			extra={"runner": runner_name},
		)
		logger.critical(
			f"Keys only in LIVE {api_verification_key_name} row:\n"
			f"{keys_only_in_live_data_dict}",
			extra={"runner": runner_name},
		)
		return False
	else:
		logger.info(
			f"Robinhood API keys for {api_verification_key_name} match.",
			extra={"runner": runner_name},
		)
		return True


def verify_dict_keys_match(dict1: dict, dict2: dict) -> bool:
	return dict1.keys() == dict2.keys()


def get_unique_keys_in_first_dict(
	default_dict: dict, other_dict: dict
) -> set[str]:
	keys_only_in_first_dict = set(default_dict) - set(other_dict)
	return keys_only_in_first_dict


def get_data_open_option_positions():
	api_data = r.get_open_option_positions()
	return api_data


def store_data_open_option_positions(api_data):
	database.update_open_option_positions(api_data)


def get_data_open_option_positions_market_data():
	option_ids = database.get_json_field_from_table_as_list(
		"open_option_positions", "json_data", "option_id"
	)

	cleaned_option_ids = []
	for option_tuple in option_ids:
		cleaned_option_ids.append(option_tuple)

	api_data = []
	for option_id in cleaned_option_ids:
		api_data.append(r.get_option_market_data_by_id(option_id)[0])

	return api_data


def store_data_open_option_positions_market_data(api_data):
	database.update_open_option_positions_market_data(api_data)


def get_data_open_broker_option_orders():
	api_data = r.get_all_open_option_orders()
	return api_data


def store_data_open_broker_option_orders(api_data):
	database.update_open_broker_option_orders(api_data)


def get_data_open_broker_option_orders_market_data():
	open_broker_option_order_legs = database.get_json_field_from_table(
		"open_broker_option_orders", "json_data", "legs"
	)
	# SAMPLE DATA open_broker_option_order_legs
	# [('[{"executions":[],"id":"69443130-4608-43c0-8ce5-1f225c685044","option":"https://api.robinhood.com/options/instruments/4aed1bc4-f8d4-48a7-a5b9-288ee30c63be/","position_effect":"close","ratio_quantity":1,"side":"sell","expiration_date":"2025-12-19","strike_price":"34.0000","option_type":"put","long_strategy_code":"4aed1bc4-f8d4-48a7-a5b9-288ee30c63be_L1","short_strategy_code":"4aed1bc4-f8d4-48a7-a5b9-288ee30c63be_S1"}]',)]
	logger.info(f"Fetched open_broker_option_orders legs: {open_broker_option_order_legs}")

	cleaned_option_leg_ids = []
	for leg in open_broker_option_order_legs:
		# SAMPLE DATA leg
		# ('[{"executions":[],"id":"69443130-4608-43c0-8ce5-1f225c685044","option":"https://api.robinhood.com/options/instruments/4aed1bc4-f8d4-48a7-a5b9-288ee30c63be/","position_effect":"close","ratio_quantity":1,"side":"sell","expiration_date":"2025-12-19","strike_price":"34.0000","option_type":"put","long_strategy_code":"4aed1bc4-f8d4-48a7-a5b9-288ee30c63be_L1","short_strategy_code":"4aed1bc4-f8d4-48a7-a5b9-288ee30c63be_S1"}]',)
		logger.info(f"leg: {leg}")

		leg = leg[0][0]
		# SAMPLE DATA leg
		# [{'executions': [], 'id': '69443130-4608-43c0-8ce5-1f225c685044', 'option': 'https://api.robinhood.com/options/instruments/4aed1bc4-f8d4-48a7-a5b9-288ee30c63be/', 'position_effect': 'close', 'ratio_quantity': 1, 'side': 'sell', 'expiration_date': '2025-12-19', 'strike_price': '34.0000', 'option_type': 'put', 'long_strategy_code': '4aed1bc4-f8d4-48a7-a5b9-288ee30c63be_L1', 'short_strategy_code': '4aed1bc4-f8d4-48a7-a5b9-288ee30c63be_S1'}]
		# leg = leg[0]
		# logger.info(f"Leg after json cleaning: {leg}")

		market_option_id = leg["option"].split("/")[5]
		cleaned_option_leg_ids.append(market_option_id)

	api_data = []
	for option_id in cleaned_option_leg_ids:
		option_market_data = r.get_option_market_data_by_id(option_id)
		option_market_data = option_market_data[0]
		api_data.append(option_market_data)

	logger.info(f"get_data_open_broker_option_orders_market_data final option market data:\n{api_data}")
	return api_data


def store_data_open_broker_option_orders_market_data(api_data):
	database.update_open_broker_option_orders_market_data(api_data)


def get_data_trigger_option_orders_market_data():
	option_ids = database.select_column_from_table("trigger_option_orders", "rh_option_uuid")

	api_data = []
	for option_id in option_ids:
		option_market_data = r.get_option_market_data_by_id(option_id)
		option_market_data = option_market_data[0]
		api_data.append(option_market_data)

	return api_data


def store_data_trigger_option_orders_market_data(api_data):
	database.update_trigger_option_orders_market_data(api_data)


def get_data_bracket_option_orders_market_data():
	option_ids = database.select_column_from_table("bracket_option_orders", "rh_option_uuid")

	api_data = []
	for option_id in option_ids:
		option_market_data = r.get_option_market_data_by_id(option_id)
		option_market_data = option_market_data[0]
		api_data.append(option_market_data)

	return api_data


def store_data_bracket_option_orders_market_data(api_data):
	database.update_bracket_option_orders_market_data(api_data)


def get_data_trailing_option_orders_market_data():
	option_ids = database.select_column_from_table("trailing_option_orders", "rh_option_uuid")

	api_data = []
	for option_id in option_ids:
		option_market_data = r.get_option_market_data_by_id(option_id)
		option_market_data = option_market_data[0]
		api_data.append(option_market_data)

	return api_data


def store_data_trailing_option_orders_market_data(api_data):
	database.update_trailing_option_orders_market_data(api_data)


def monitor_bracket_option_orders():
	pass


# WORKING
def monitor_trailing_option_orders(runner_name):
	trailing_orders = database.get_trailing_option_orders_list()

	for order in trailing_orders:
		logger.info(f"Monitoring trailing option order: {order}", extra={"runner": runner_name})

		if order["executed"]:
			logger.info(
				f"Trailing order #{order["order_id_pk"]} already executed. Skipping monitor.", 
				extra={"runner": runner_name}
			)
			continue

		option_market_row = database.get_trailing_option_order_market_data_by_order_uuid(order["rh_option_uuid"])
		logger.info(
			f"Fetched option market data for trailing order {order['order_id_pk']}: {option_market_row}", 
			extra={"runner": runner_name}
		)
		if option_market_row == None:
			logger.info(
				f"No market data found for {order["rh_option_uuid"]}. Skipping this order.", 
				extra={"runner": runner_name}
			)
			continue
		# {'order_id_pk': 1, 'active': True, 'epoch_time_created_at': 1768274200.0, 'executed': False, 'execute_only_after_trigger_order_ids': [], 'execute_only_after_bracket_order_ids': [], 'execute_only_after_trailing_order_ids': [], 'execution_deactivates_trigger_order_ids': [], 'execution_deactivates_bracket_order_ids': [], 'execution_deactivates_trailing_order_ids': [], 'buy_or_sell': 'sell', 'credit_or_debit': 'credit', 'symbol': 'IWM', 'strike': 258.0, 'call_or_put': 'put', 'expiration_date': '2026-03-20', 'rh_option_uuid': 'ee1be306-02bb-416d-aef5-cb964a76e4e7', 'quantity': 1, 'message_on_success': 'success msg', 'message_on_failure': 'failure msg', 'below_tick': 0.01, 'above_tick': 0.01, 'cutoff_price': 0.0, 'max_order_attempts': 10, 'emergency_order_fill_on_failure': True, 'percent_from_high_sell_trigger': 0.15, 'sell_at_specific_price': 0.25, 'highest_price_since_order_placed': NoneAND active=TRUE}

		# {'option_uuid_pk': 'ee1be306-02bb-416d-aef5-cb964a76e4e7', 'json_data': {'rho': '-0.183402', 'vega': '0.430015', 'delta': '-0.396893', 'gamma': '0.017277', 'state': 'active', 'theta': '-0.055987', 'symbol': 'IWM', 'volume': 136, 'ask_size': 56, 'bid_size': 132, 'ask_price': '6.740000', 'bid_price': '6.680000', 'low_price': '7.440000', 'high_price': '8.100000', 'instrument': 'https://api.robinhood.com/options/instruments/ee1be306-02bb-416d-aef5-cb964a76e4e7/', 'mark_price': '6.710000', 'occ_symbol': 'IWM   260320P00258000', 'updated_at': '2026-01-12T21:14:59.686979751Z', 'instrument_id': 'ee1be306-02bb-416d-aef5-cb964a76e4e7', 'open_interest': 93, 'pricing_model': 'Bjerksund-Stensland 1993', 'last_trade_size': 59, 'break_even_price': '251.290000', 'last_trade_price': '7.460000', 'implied_volatility': '0.204667', 'adjusted_mark_price': '6.710000', 'previous_close_date': '2026-01-09', 'previous_close_price': '7.200000', 'chance_of_profit_long': '0.313193', 'chance_of_profit_short': '0.686807', 'low_fill_rate_buy_price': '6.699000', 'high_fill_rate_buy_price': '6.727000', 'low_fill_rate_sell_price': '6.720000', 'high_fill_rate_sell_price': '6.692000', 'adjusted_mark_price_round_down': '6.710000'}, 'still_alive': True, 'last_update_epoch_time': 1768274200.0}

		highest_price_since_order_placed = float(order["highest_price_since_order_placed"])
		current_mark_price = float(option_market_row["json_data"]["mark_price"])

		if current_mark_price > highest_price_since_order_placed:
			logger.info(f"New highest_price_since_order_placed for order {order['order_id_pk']}")
			highest_price_since_order_placed = current_mark_price
			conn = database.get_database_connection()
			cur = conn.cursor()
			sql_query = "UPDATE trailing_option_orders SET highest_price_since_order_placed=%s WHERE order_id_pk=%s;"
			values = (highest_price_since_order_placed, order['order_id_pk'])
			cur.execute(sql_query, values)
			conn.commit()
			cur.close()
			conn.close()

		percent_from_high_sell_trigger = float(order["percent_from_high_sell_trigger"])
		sell_at_specific_price = float(order["sell_at_specific_price"])

		execute_order = False
		if current_mark_price < highest_price_since_order_placed * percent_from_high_sell_trigger:
			execute_order = True
		if current_mark_price >= sell_at_specific_price:
			execute_order = True

		execution_requires_trigger_order_ids = order["execute_only_after_trigger_order_ids"]
		execution_requires_bracket_order_ids = order["execute_only_after_bracket_order_ids"]
		execution_requires_trailing_order_ids = order["execute_only_after_trailing_order_ids"]
		logger.info("Checking that required previous orders have been executed.")
		# get executed status of prior orders to see if valid
		executed_statuses_list = database.get_executed_status_orders(
			execution_requires_trigger_order_ids,
			execution_requires_bracket_order_ids,
			execution_requires_trailing_order_ids
		)
		logger.info(f"Executed statuses list: {executed_statuses_list}", extra={"runner": runner_name})
		for order_executed in executed_statuses_list:
			if order_executed == False:
				execute_order = False

		if order["executed"] == True:
			execute_order = False

		if order["active"] == False:
			execute_order = False

		execution_deactivates_trigger_order_ids = order["execution_deactivates_trigger_order_ids"]
		execution_deactivates_bracket_order_ids = order["execution_deactivates_bracket_order_ids"]
		execution_deactivates_trailing_order_ids = order["execution_deactivates_trailing_order_ids"]
		if execute_order:
			try:
				database.mark_order_executed(table="trailing_option_orders", order_id_pk=order["order_id_pk"])
				database.deactivate_orders(
					execution_deactivates_trigger_order_ids, 
					execution_deactivates_bracket_order_ids, 
					execution_deactivates_trailing_order_ids
				)
				orders.execute_market_sell(order)
				logger.info(f"Executed sell for trailing order #{orders['order_id_pk']}")
			except Exception as e:
				logger.critical(f"Issue in selling trailing order #{orders['order_id_pk']}")



def start_data_fetch_runner(runner_dict):
	logger.info(
		f"Starting data fetch runner: {runner_dict['runner_name']}.",
		extra={"runner": runner_dict["runner_name"]},
	)

	runner = DataFetchRunner(runner_dict)
	runner.write_runner_status()

	while True:
		runner.status = runner.get_runner_status()
		logger.info(
			f"Runner status: {runner.status}",
			extra={"runner": runner.status["runner_name_pk"]},
		)

		if runner.status["active"] == False:
			runner.status["current_update_success"] = False
			runner.status["previous_update_success"] = False
			runner.write_runner_status()
			logger.info(
				f"Runner {runner.status['runner_name_pk']} is not active. Sleeping for default_interval.",
				extra={"runner": runner.status["runner_name_pk"]},
			)
			time.sleep(runner.status["default_interval"])
			continue
		else:
			logger.info(
				f"Runner {runner.status['runner_name_pk']} is active. Continuing API fetch.",
				extra={"runner": runner.status["runner_name_pk"]},
			)

		runner.status["current_update_success"] = False
		runner.write_runner_status()

		try:
			api_data = runner.get_data()
			logger.info(
				f"Runner {runner.status['runner_name_pk']} api_data: {api_data}",
				extra={"runner": runner.status["runner_name_pk"]},
			)
		except Exception as e:
			logger.exception(
				f"{e}",
				stack_info=True,
				extra={"runner": runner.status["runner_name_pk"]},
			)

			runner.status["current_update_success"] = False
			runner.status["previous_update_success"] = False
			runner.status["adjusted_interval"] += config.RUNNER_FAILURE_ADJUSTMENT
			if runner.status["adjusted_interval"] > config.MAXIMUM_REFRESH_INTERVAL:
				runner.status["adjusted_interval"] = config.MAXIMUM_REFRESH_INTERVAL

			runner.write_runner_status()
			time.sleep(runner.status["adjusted_interval"])
			continue

		api_data_match = None
		if len(api_data) > 0:
			logger.info(
				f"Entering verification for {runner.status['runner_name_pk']}",
				extra={"runner": runner.status["runner_name_pk"]},
			)
			api_data_match = runner.verify_data(api_data[0])
		else:
			logger.info(
				f"No API data to verify.",
				extra={"runner": runner.status["runner_name_pk"]},
			)

		if api_data_match == True:
			logger.info(
				f"API data for {runner.status['runner_name_pk']} matches default record.",
				extra={"runner": runner.status["runner_name_pk"]},
			)
		if api_data_match == False:
			logger.critical(
				f"API data for {runner.status['runner_name_pk']} does not match default records. There was an API change from Robinhood.",
				extra={"runner": runner.status["runner_name_pk"]},
			)

		try:
			runner.store_data(api_data)
			runner.status["current_update_success"] = True
			runner.status["previous_update_success"] = True
			runner.status["epoch_time_previous_success"] = time.time()
			if runner.status["adjusted_interval"] > runner.status["default_interval"]:
				runner.status["adjusted_interval"] -= config.RUNNER_SUCCESS_ADJUSTMENT
			if runner.status["adjusted_interval"] < runner.status["default_interval"]:
				runner.status["adjusted_interval"] = runner.status["default_interval"]

			time.sleep(runner.status["adjusted_interval"])
			runner.write_runner_status()
			continue
		except Exception as e:
			logger.exception(
				f"{e}",
				stack_info=True,
				extra={"runner": runner.status["runner_name_pk"]},
			)
			time.sleep(runner.status["adjusted_interval"])
			continue


def start_monitor_runner(runner_dict):
	logger.info(
		f"Starting monitor runner: {runner_dict['runner_name']}.",
		extra={"runner": runner_dict["runner_name"]},
	)

	runner = MonitorRunner(runner_dict)
	runner.write_runner_status()

	while True:
		runner.status = runner.get_runner_status()
		logger.info(
			f"Runner status: {runner.status}",
			extra={"runner": runner.status["runner_name_pk"]},
		)

		if runner.status["active"] == False:
			runner.status["current_update_success"] = False
			runner.status["previous_update_success"] = False
			runner.write_runner_status()
			logger.info(
				f"Runner {runner.status['runner_name_pk']} is not active. Sleeping for default_interval.",
				extra={"runner": runner.status["runner_name_pk"]},
			)
			time.sleep(runner.status["default_interval"])
			continue
		else:
			logger.info(
				f"Runner {runner.status['runner_name_pk']} is active. Continuing monitoring.",
				extra={"runner": runner.status["runner_name_pk"]},
			)

		runner.status["current_update_success"] = False
		runner.write_runner_status()

		try:
			runner_dict["monitor_function"](runner_dict['runner_name'])
			runner.status["current_update_success"] = True
			runner.status["previous_update_success"] = True
			runner.status["epoch_time_previous_success"] = time.time()
			runner.write_runner_status()
			time.sleep(runner.status["default_interval"])
			continue
		except Exception as e:
			logger.exception(
				f"{e}",
				stack_info=True,
				extra={"runner": runner.status["runner_name_pk"]},
			)
			runner.status["current_update_success"] = False
			runner.status["previous_update_success"] = False
			runner.write_runner_status()
			time.sleep(runner.status["default_interval"])
			continue


def main():
	database.logger = logging.getLogger("runners")

	r.login(config.ROBINHOOD_USERNAME, config.ROBINHOOD_PASSWORD)
	orders.robinhood_login()


	# for dev only, refactor later
	database.drop_all_tables()
	database.create_all_tables()

	orders.create_trigger_option_order(
		active=True,
		epoch_time_created_at=time.time(),
		execute_only_after_trigger_order_ids=[],
		execute_only_after_bracket_order_ids=[],
		execute_only_after_trailing_order_ids=[],
		execution_deactivates_trigger_order_ids=[],
		execution_deactivates_bracket_order_ids=[],
		execution_deactivates_trailing_order_ids=[],
		buy_or_sell="buy",
		credit_or_debit="debit",
		symbol="IWM",
		strike=258,
		call_or_put="call",
		expiration_date="2026-03-20",
		quantity=1,
		message_on_success="success msg",
		message_on_failure="failure msg",
		max_order_attempts=10,
		emergency_order_fill_on_failure=True,
		trigger_order_uuid=str(uuid.uuid4())
	)

	# orders.create_trigger_option_order(
	# 	active=True,
	# 	epoch_time_created_at=time.time(),
	# 	execute_only_after_trigger_order_ids=[],
	# 	execute_only_after_bracket_order_ids=[],
	# 	execute_only_after_trailing_order_ids=[],
	# 	execution_deactivates_trigger_order_ids=[],
	# 	execution_deactivates_bracket_order_ids=[],
	# 	execution_deactivates_trailing_order_ids=[],
	# 	buy_or_sell="buy",
	# 	credit_or_debit="debit",
	# 	symbol="IWM",
	# 	strike=258,
	# 	call_or_put="call",
	# 	expiration_date="2026-03-20",
	# 	quantity=1,
	# 	message_on_success="success msg",
	# 	message_on_failure="failure msg",
	# 	max_order_attempts=10,
	# 	emergency_order_fill_on_failure=True,
	# 	trigger_order_uuid=str(uuid.uuid4())
	# )

	# orders.create_bracket_option_order(
	#     active=True,
    #     epoch_time_created_at=time.time(),
    #     execute_only_after_trigger_order_ids=[],
    #     execute_only_after_bracket_order_ids=[],
    #     execute_only_after_trailing_order_ids=[],
    #     execution_deactivates_trigger_order_ids=[],
    #     execution_deactivates_bracket_order_ids=[],
    #     execution_deactivates_trailing_order_ids=[],
    #     buy_or_sell="sell",
    #     credit_or_debit="credit",
    #     symbol="IWM",
    #     strike="258",
    #     call_or_put="put",
    #     expiration_date="2026-03-20",
    #     quantity=1,
    #     high_sell_mark_price=0.20,
    #     low_sell_mark_price=0.15,
    #     message_on_success="success msg",
    #     message_on_failure="failure msg",
    #     max_order_attempts=10,
    #     emergency_order_fill_on_failure=True
	# )

	orders.create_trailing_option_sell_order(
		active=True, 
		epoch_time_created_at=time.time(), 
		executed=False, 
		execute_only_after_trigger_order_ids=[], 
		execute_only_after_bracket_order_ids=[], 
		execute_only_after_trailing_order_ids=[], 
		execution_deactivates_trigger_order_ids=[], 
		execution_deactivates_bracket_order_ids=[], 
		execution_deactivates_trailing_order_ids=[], 
		quantit=1,
		symbol="IWM",
		call_or_put="call",
		expiration_date="2026-03-20",
		strike=258,
		message_on_success="success msg",
		message_on_failure="failure msg",
		max_order_attempts=10,
		emergency_order_fill_on_failure=True, 
		percent_from_high_sell_trigger=.90,
		sell_at_specific_price=18.00,
		purchase_price: 2.00,
	)

	max_workers = len(schema.RUNNERS)
	with ThreadPoolExecutor(max_workers=max_workers) as runner_threads:
		logger.info("Starting runners.")
		for runner in schema.RUNNERS:
			# start_runner(runner)
			if runner["type"] == "data_fetch":
				runner_threads.submit(start_data_fetch_runner, runner)
			if runner["type"] == "monitor":
				runner_threads.submit(start_monitor_runner, runner)


if __name__ == "__main__":
	main()
