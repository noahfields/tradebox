from concurrent.futures import ThreadPoolExecutor
import logging
import time

import robin_stocks.robinhood as r

import config
import database
import log
import robinhood_api

logger = log.setup_logger("runners")

# RUNNERS = {
# 	"runner_update_open_option_positions": config.OPEN_POSITIONS_REFRESH_INTERVAL,
# 	"runner_update_open_option_positions_market_data": config.MARKET_DATA_REFRESH_INTERVAL,
# 	# "runner_update_open_broker_option_orders": config.BROKER_ORDERS_REFRESH_INTERVAL,
# 	# "runner_update_open_broker_option_orders_market_data": config.MARKET_DATA_REFRESH_INTERVAL,
# 	# "runner_update_trigger_option_orders_market_data": config.MARKET_DAT

RUNNERS = [
	{ 
		"runner_name": "open_option_positions",
		"active": True
		"get_data_function": "get_data_open_option_positions",
		"verify_data_keyset": "get_open_option_positions",
		"store_data_function": "store_data_open_option_positions",
		"default_interval": config.OPEN_POSITIONS_REFRESH_INTERVAL,
	},
]

API_VERIFICATION_DEFAULT_KEYSETS = {
	"get_open_option_positions": {'account': 'https://api.robinhood.com/accounts/5QU45833/', 'account_number': '5QU45833', 'average_price': '-16.0000', 'chain_id': '72362eb7-bc7c-4d10-9be4-48a53fffd101', 'chain_symbol': 'IWM', 'id': '876c8360-ce18-4c31-b31f-e760270b091d', 'option': 'https://api.robinhood.com/options/instruments/2b4dde4d-c7b7-4c6c-8290-a70f76cedaf9/', 'type': 'short', 'pending_buy_quantity': '0.0000', 'pending_expired_quantity': '0.0000', 'pending_expiration_quantity': '0.0000', 'pending_exercise_quantity': '0.0000', 'pending_assignment_quantity': '0.0000', 'pending_sell_quantity': '0.0000', 'quantity': '17.0000', 'intraday_quantity': '17.0000', 'intraday_average_open_price': '-16.0000', 'created_at': '2025-12-19T21:09:50.112600Z', 'expiration_date': '2025-12-22', 'trade_value_multiplier': '100.0000', 'updated_at': '2025-12-19T21:09:50.501378Z', 'url': 'https://api.robinhood.com/options/positions/876c8360-ce18-4c31-b31f-e760270b091d/', 'option_id': '2b4dde4d-c7b7-4c6c-8290-a70f76cedaf9', 'clearing_running_quantity': '17.0000', 'clearing_cost_basis': '272.0000', 'clearing_direction': 'credit', 'clearing_intraday_running_quantity': '17.0000', 'clearing_intraday_cost_basis': '272.0000', 'clearing_intraday_direction': 'credit', 'opened_at': '2025-12-19T21:09:50.116471Z'},

	"get_option_market_data_by_id": {'adjusted_mark_price': '0.200000', 'adjusted_mark_price_round_down': '0.200000', 'ask_price': '0.210000', 'ask_size': 2, 'bid_price': '0.190000', 'bid_size': 98, 'break_even_price': '248.800000', 'high_price': '1.330000', 'instrument': 'https://api.robinhood.com/options/instruments/2b4dde4d-c7b7-4c6c-8290-a70f76cedaf9/', 'instrument_id': '2b4dde4d-c7b7-4c6c-8290-a70f76cedaf9', 'last_trade_price': '0.210000', 'last_trade_size': 1, 'low_price': '0.160000', 'mark_price': '0.200000', 'open_interest': 1473, 'previous_close_date': '2025-12-18', 'previous_close_price': '1.810000', 'updated_at': '2025-12-19T21:14:59.805486725Z', 'volume': 9984, 'symbol': 'IWM', 'occ_symbol': 'IWM   251222P00249000', 'state': 'active', 'chance_of_profit_long': '0.159818', 'chance_of_profit_short': '0.840182', 'delta': '-0.183593', 'gamma': '0.133426', 'implied_volatility': '0.117049', 'rho': '-0.002116', 'theta': '-0.152646', 'vega': '0.045217', 'pricing_model': 'Bjerksund-Stensland 1993', 'high_fill_rate_buy_price': '0.205000', 'high_fill_rate_sell_price': '0.194000', 'low_fill_rate_buy_price': '0.195000', 'low_fill_rate_sell_price': '0.204000'},

	"get_all_open_option_orders": {'account_number': '5QU45833', 'cancel_url': 'https://api.robinhood.com/options/orders/694781e4-11ef-4af7-b3cc-a739ccec0da3/cancel/', 'canceled_quantity': '0.00000', 'created_at': '2025-12-21T05:13:08.046546Z', 'direction': 'debit', 'id': '694781e4-11ef-4af7-b3cc-a739ccec0da3', 'legs': [{'executions': [], 'id': '694781e4-0f2f-4fee-bc09-97f3c2c8c0d9', 'option': 'https://api.robinhood.com/options/instruments/4e188c22-aef8-4f43-8dd0-411acc486654/', 'position_effect': 'open', 'ratio_quantity': 1, 'side': 'buy', 'expiration_date': '2025-12-23', 'strike_price': '255.0000', 'option_type': 'call', 'long_strategy_code': '4e188c22-aef8-4f43-8dd0-411acc486654_L1', 'short_strategy_code': '4e188c22-aef8-4f43-8dd0-411acc486654_S1'}], 'pending_quantity': '2.00000', 'premium': '3.00000000', 'processed_premium': '0', 'processed_premium_direction': 'debit', 'market_hours': 'regular_hours', 'net_amount': '0', 'net_amount_direction': 'debit', 'price': '0.03000000', 'processed_quantity': '0.00000', 'quantity': '2.00000', 'ref_id': 'dd0c09ef-716c-4261-953d-62a7259fbea8', 'regulatory_fees': '0', 'contract_fees': '0', 'gold_savings': '0', 'state': 'queued', 'time_in_force': 'gfd', 'trigger': 'immediate', 'type': 'limit', 'updated_at': '2025-12-21T05:13:08.384132Z', 'chain_id': '72362eb7-bc7c-4d10-9be4-48a53fffd101', 'chain_symbol': 'IWM', 'response_category': None, 'opening_strategy': 'long_call', 'closing_strategy': None, 'stop_price': None, 'form_source': 'option_chain', 'client_bid_at_submission': '0.11000000', 'client_ask_at_submission': '0.13000000', 'client_time_at_submission': None, 'average_net_premium_paid': '0.00000000', 'estimated_total_net_amount': '6.04', 'estimated_total_net_amount_direction': 'debit', 'is_replaceable': True, 'strategy': 'long_call', 'derived_state': 'queued', 'sales_taxes': []},
}

class Runner:
	def __init__(self, runner_dict):
		self.get_data_function_name = runner_dict["get_data_function"]
		self.store_data_function_name = runner_dict["store_data_function"]
		self.verify_data_keyset = runner_dict["verify_data_keyset"]


		self.status = { 
			"runner_name_pk": runner_dict["runner_name"],
			"active": runner_dict["active"],
			"adjusted_interval": runner_dict["default_interval"],
			"default_interval": runner_dict["default_interval"],
			"current_update_success": False,
			"previous_update_success": False,
			"epoch_time_previous_success": 0
		}

	def get_data(self):
		api_data = eval(f"{self.get_data_function_name}()")
		return api_data
	
	def verify_data(self, api_data_row: dict):
		match_bool = verify_api_key_match(self.verify_data_keyset, api_data_row)
		return match_bool
	
	def store_data(self, api_data) -> None:
		eval(f"{self.store_data_function_name}()")
	
	def get_runner_status(self):
		status = database.get_runner_status(self.status["runner_name_pk"])
		return status

	def write_runner_status(self):
		database.write_runner_status(self.status)


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


def get_data_open_option_positions():
	api_data = robinhood_api.getu_open_option_positions()
	return api_data

def verify_data_open_option_positions():
	pass

def store_data_open_option_positions(api_data) -> None:
	database.store_open_option_positions(api_data)


def loop_runner(runner_name):
	while True:
		logger.info(f"Starting execution loop for {runner_name}.")

		runner_info = database.get_runner_info(runner_name)
		updated_runner_info = runner_info.copy()

		logger.info(f"Successfully received {runner_name} runner_info: {runner_info}")

		if not runner_info["active"]:
			logger.info(f"Runner {runner_name} is not active.")

			updated_runner_info["current_update_success"] = 0
			updated_runner_info["last_update_success"] = 0

			logger.info(
				f"Saving updated_runner_info for {runner_name}: "
				f"{updated_runner_info}"
			)
			database.update_runner(updated_runner_info)

			time.sleep(updated_runner_info["adjusted_interval"])
			logger.info(
				f"Concluded interval pause of "
				f"{updated_runner_info['adjusted_interval']} seconds "
				f"for {runner_name}."
			)
			continue

		updated_runner_info["current_update_success"] = 0
		logger.info(
			f"Marking {runner_name} for failure: "
			f"setting current_update_success to "
			f"{updated_runner_info['current_update_success']}"
		)
		database.update_runner(updated_runner_info)

		success = eval(f"{runner_name}()")

		if success:
			if updated_runner_info["adjusted_interval"] > updated_runner_info["default_interval"]:
				updated_runner_info["adjusted_interval"] = updated_runner_info["adjusted_interval"] - 1

			updated_runner_info["current_update_success"] = 1
			updated_runner_info["last_update_success"] = 1
			updated_runner_info["last_successful_update_epoch_time"] = time.time()

			logger.info(
				f"Updating {runner_name} record. Record details for update:\n"
				f"{updated_runner_info}"
			)
			database.update_runner(updated_runner_info)

			time.sleep(updated_runner_info["adjusted_interval"])
			logger.info(
				f"Runner {runner_name} paused for "
				f"{updated_runner_info['adjusted_interval']} seconds."
			)
		else:
			logger.info(
				f"Changing adjusted_intveral from "
				f"{updated_runner_info['adjusted_interval']} to "
				f"{updated_runner_info['adjusted_interval'] + 1} seconds."
			)
			updated_runner_info["adjusted_interval"] = runner_info["adjusted_interval"] + 5

			if updated_runner_info["adjusted_interval"] >= config.MAXIMUM_INTERVAL:
				updated_runner_info["adjusted_interval"] = config.MAXIMUM_INTERVAL
			logger.info(
				f"Final decision on adjusted_interval: "
				f"{updated_runner_info['adjusted_interval']} seconds"
			)

			updated_runner_info["current_update_success"] = 0
			updated_runner_info["last_update_success"] = 0

			logger.info(
				f"Updating {runner_name} record. Record details for update:\n"
				f"{updated_runner_info}"
			)
			database.update_runner(updated_runner_info)

			time.sleep(updated_runner_info["adjusted_interval"])
			logger.debug(
				f"Runner {runner_info} paused for {updated_runner_info['adjusted_interval']} seconds."
			)

def start_runner(runner_dict):
	logger.info(f"Starting runner: {runner['runner_name']}.")

	runner = Runner(runner_dict)
	runner.write_runner_status()

	while True:
		runner.status = runner.get_current_runner_status()

		if not runner.status["active"]:
			runner.status["current_update_success"] = False
			runner.status["previous_update_success"] = False
			runner.write_runner_status()
			time.sleep(runner.status["default_interval"])
			continue

		runner.status["current_update_success"] = False
		runner.write_runner_status()

		try:
			api_data = runner.get_data()
		except Exception as e:
			logger.exception(stack_info=True)
			runner.status["current_update_success"] = False
			runner.status["previous_update_success"] = False
			runner.status["adjusted_interval"] += config.RUNNER_FAILURE_ADJUSTMENT
			if runner.status["adjusted_interval"] > config.MAXIMUM_REFRESH_INTERVAL:
				runner.status["adjusted_interval"] = config.MAXIMUM_REFRESH_INTERVAL
			runner.write_runner_status()
			time.sleep(runner.status["adjusted_interval"])
			continue

		if len(api_data) > 0:
			data_match_true = runner.verify_data(api_data[0])

		if not data_match_true:
			logger.critical(f"API data for {runner.status["runner_name_pk"]} does not match default records. There was an API change from Robinhood.")
		
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
		except:
			logger.exception(stack_info=True)
			continue


def main():
	database.logger = logging.getLogger("runners")
	robinhood_api.logger = logging.getLogger("runners")

	r.login(config.ROBINHOOD_USERNAME, config.ROBINHOOD_PASSWORD)

	# for dev only, refactor later
	database.delete_all_tables()
	database.create_all_tables()

	max_workers = len(RUNNERS)
	with ThreadPoolExecutor(max_workers=max_workers) as runner_threads:
		logger.info("Starting runners.")
		for runner in RUNNERS:
			runner_threads.submit(start_runner, runner)


if __name__ == "__main__":
	main()
