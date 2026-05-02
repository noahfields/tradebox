import json
import logging
import sys
import time
import uuid
import datetime

import robin_stocks.robinhood as r

import config
import database
import log
import orders
import schema

logger = None


API_VERIFICATION_DEFAULT_KEYSETS = {
    "get_portfolio_profile": {
        "url": "https://api.robinhood.com/portfolios/5QU45833/",
        "account": "https://api.robinhood.com/accounts/5QU45833/",
        "start_date": "2015-12-09",
        "market_value": "0.0000",
        "equity": "1979.7400",
        "extended_hours_market_value": "0.0000",
        "extended_hours_equity": "1979.7400",
        "extended_hours_portfolio_equity": "1979.7400",
        "last_core_market_value": "0.0000",
        "last_core_equity": "1979.7400",
        "last_core_portfolio_equity": "1979.7400",
        "excess_margin": "None",
        "excess_maintenance": "None",
        "excess_margin_with_uncleared_deposits": "None",
        "excess_maintenance_with_uncleared_deposits": "None",
        "equity_previous_close": "815.7000",
        "portfolio_equity_previous_close": "815.7000",
        "adjusted_equity_previous_close": "815.7000",
        "adjusted_portfolio_equity_previous_close": "815.7000",
        "withdrawable_amount": "0.22",
        "unwithdrawable_deposits": "0.0000",
        "unwithdrawable_grants": "0.0000",
        "is_primary_account": "True",
        "non_usd_currency_equity": "0.0000",
    },
    "get_open_option_positions": {
        "account": "https://api.robinhood.com/accounts/5QU45833/",
        "account_number": "5QU45833",
        "average_price": "77.2500",
        "chain_id": "9ee49197-7b3c-46c2-8d83-5d5ad1ed9eaa",
        "chain_symbol": "TSLA",
        "id": "b772c105-3908-42e4-a741-7bf893465f06",
        "option": "https://api.robinhood.com/options/instruments/d14e47f4-8980-4893-a478-fa92f2229c8c/",
        "type": "long",
        "pending_buy_quantity": "0.0000",
        "pending_expired_quantity": "4.0000",
        "pending_expiration_quantity": "4.0000",
        "pending_exercise_quantity": "0.0000",
        "pending_assignment_quantity": "0.0000",
        "pending_sell_quantity": "0.0000",
        "quantity": "4.0000",
        "intraday_quantity": "4.0000",
        "intraday_average_open_price": "77.2500",
        "created_at": "2026-04-27T15:01:17.378339Z",
        "expiration_date": "2026-04-27",
        "trade_value_multiplier": "100.0000",
        "updated_at": "2026-04-27T20:15:57.364794Z",
        "url": "https://api.robinhood.com/options/positions/b772c105-3908-42e4-a741-7bf893465f06/",
        "option_id": "d14e47f4-8980-4893-a478-fa92f2229c8c",
        "clearing_running_quantity": "0",
        "clearing_cost_basis": "0",
        "clearing_direction": "debit",
        "clearing_intraday_running_quantity": "0",
        "clearing_intraday_cost_basis": "0",
        "clearing_intraday_direction": "debit",
        "opened_at": "2026-04-27T15:01:17.391212Z",
    },
    "get_option_market_data_by_id": {
        "adjusted_mark_price": "16.760000",
        "adjusted_mark_price_round_down": "16.750000",
        "ask_price": "17.000000",
        "ask_size": "50",
        "bid_price": "16.510000",
        "bid_size": "6",
        "break_even_price": "291.760000",
        "high_price": "17.440000",
        "instrument": "https://api.robinhood.com/options/instruments/983df2b0-0731-4101-8267-98264969296a/",
        "instrument_id": "983df2b0-0731-4101-8267-98264969296a",
        "last_trade_price": "16.520000",
        "last_trade_size": "3",
        "low_price": "16.520000",
        "mark_price": "16.755000",
        "open_interest": "2183",
        "previous_close_date": "2026-04-24",
        "previous_close_price": "16.300000",
        "updated_at": "2026-04-27T20:14:59.990401321Z",
        "volume": "313",
        "symbol": "IWM",
        "occ_symbol": "IWM   260821C00275000",
        "state": "active",
        "chance_of_profit_long": "0.353361",
        "chance_of_profit_short": "0.646639",
        "delta": "0.585157",
        "gamma": "0.011024",
        "implied_volatility": "0.226572",
        "rho": "0.460765",
        "theta": "-0.074250",
        "vega": "0.608111",
        "pricing_model": "Bjerksund-Stensland 1993",
        "high_fill_rate_buy_price": "16.872000",
        "high_fill_rate_sell_price": "16.637000",
        "low_fill_rate_buy_price": "16.631000",
        "low_fill_rate_sell_price": "16.878000",
    },
    "get_option_instrument_data_by_id": {
        "chain_id": "72362eb7-bc7c-4d10-9be4-48a53fffd101",
        "chain_symbol": "IWM",
        "created_at": "2025-12-18T03:13:36.785410Z",
        "expiration_date": "2026-08-21",
        "id": "983df2b0-0731-4101-8267-98264969296a",
        "issue_date": "2025-12-18",
        "min_ticks": "{'above_tick': '0.01', 'below_tick': '0.01', 'cutoff_price': '0.00'}",
        "rhs_tradability": "tradable",
        "state": "active",
        "strike_price": "275.0000",
        "tradability": "tradable",
        "type": "call",
        "updated_at": "2025-12-18T03:13:36.785414Z",
        "url": "https://api.robinhood.com/options/instruments/983df2b0-0731-4101-8267-98264969296a/",
        "sellout_datetime": "2026-08-21T19:45:00+00:00",
        "long_strategy_code": "983df2b0-0731-4101-8267-98264969296a_L1",
        "short_strategy_code": "983df2b0-0731-4101-8267-98264969296a_S1",
        "underlying_type": "equity",
    },
    "get_all_open_option_orders": {
        "account_number": "5QU45833",
        "cancel_url": "https://api.robinhood.com/options/orders/69f02f9e-89f9-4700-ba6d-c98db3e133e6/cancel/",
        "canceled_quantity": "0.00000",
        "created_at": "2026-04-28T03:55:10.222563Z",
        "direction": "debit",
        "id": "69f02f9e-89f9-4700-ba6d-c98db3e133e6",
        "legs": "[{'executions': [], 'id': '69f02f9e-8a3c-4c8d-9de3-eb45fe71d2d2', 'option': 'https://api.robinhood.com/options/instruments/fb4c92b3-1c5b-40ec-9e47-0f7b9e938434/', 'position_effect': 'open', 'ratio_quantity': 1, 'side': 'buy', 'expiration_date': '2026-04-28', 'strike_price': '278.0000', 'option_type': 'call', 'long_strategy_code': 'fb4c92b3-1c5b-40ec-9e47-0f7b9e938434_L1', 'short_strategy_code': 'fb4c92b3-1c5b-40ec-9e47-0f7b9e938434_S1'}]",
        "pending_quantity": "1.00000",
        "premium": "1.00000000",
        "processed_premium": "0",
        "processed_premium_direction": "debit",
        "market_hours": "regular_hours",
        "net_amount": "0",
        "net_amount_direction": "debit",
        "price": "0.01000000",
        "processed_quantity": "0.00000",
        "quantity": "1.00000",
        "ref_id": "3e714b1b-eb48-4b08-a3e0-8dade0a51eb7",
        "regulatory_fees": "0",
        "contract_fees": "0",
        "gold_savings": "0",
        "state": "queued",
        "time_in_force": "gtc",
        "trigger": "immediate",
        "type": "limit",
        "updated_at": "2026-04-28T03:55:10.569937Z",
        "chain_id": "72362eb7-bc7c-4d10-9be4-48a53fffd101",
        "chain_symbol": "IWM",
        "trade_value_multiplier": "100.0000",
        "response_category": "None",
        "opening_strategy": "long_call",
        "closing_strategy": "None",
        "stop_price": "None",
        "form_source": "option_chain",
        "client_bid_at_submission": "0.64000000",
        "client_ask_at_submission": "0.65000000",
        "client_time_at_submission": "None",
        "average_net_premium_paid": "0.00000000",
        "estimated_total_net_amount": "1.04",
        "estimated_total_net_amount_direction": "debit",
        "estimated_total_net_amount_v2": "1.04",
        "estimated_total_net_amount_direction_v2": "debit",
        "is_replaceable": "True",
        "strategy": "long_call",
        "derived_state": "queued",
        "sales_taxes": "[]",
    },
}

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


def get_data_portfolio_profile():
	api_data = r.load_portfolio_profile()
	return api_data


def store_data_portfolio_profile(api_data):
	database.update_portfolio_profile(api_data)


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


def get_data_open_option_positions_instrument_data():
	option_ids = database.get_json_field_from_table_as_list(
		"open_option_positions", "json_data", "option_id"
	)

	cleaned_option_ids = []
	for option_tuple in option_ids:
		cleaned_option_ids.append(option_tuple)

	api_data = []
	for option_id in cleaned_option_ids:
		api_data.append(r.get_option_instrument_data_by_id(option_id))

	return api_data


def store_data_open_option_positions_instrument_data(api_data):
	database.update_open_option_positions_instrument_data(api_data)


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


def get_data_open_broker_option_orders_instrument_data():
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
		option_instrument_data = r.get_option_instrument_data_by_id(option_id)
		api_data.append(option_instrument_data)

	logger.info(f"get_data_open_broker_option_orders_instrument_data final instrument market data:\n{api_data}")
	return api_data


def store_data_open_broker_option_orders_instrument_data(api_data):
	database.update_open_broker_option_orders_instrument_data(api_data)


def get_data_trigger_option_orders_market_data():
	option_ids = database.select_column_from_table("trigger_option_orders", "robinhood_option_uuid")

	api_data = []
	for option_id in option_ids:
		option_market_data = r.get_option_market_data_by_id(option_id)
		option_market_data = option_market_data[0]
		api_data.append(option_market_data)

	return api_data


def store_data_trigger_option_orders_market_data(api_data):
	database.update_trigger_option_orders_market_data(api_data)


def get_data_bracket_option_orders_market_data():
	option_ids = database.select_column_from_table("bracket_option_orders", "robinhood_option_uuid")

	api_data = []
	for option_id in option_ids:
		option_market_data = r.get_option_market_data_by_id(option_id)
		option_market_data = option_market_data[0]
		api_data.append(option_market_data)

	return api_data


def store_data_bracket_option_orders_market_data(api_data):
	database.update_bracket_option_orders_market_data(api_data)


def get_data_trailing_sell_option_orders_market_data():
	option_ids = database.select_column_from_table("trailing_sell_option_orders", "robinhood_option_uuid")

	api_data = []
	for option_id in option_ids:
		option_market_data = r.get_option_market_data_by_id(option_id)
		option_market_data = option_market_data[0]
		api_data.append(option_market_data)

	return api_data




def store_data_trailing_sell_option_orders_market_data(api_data):
	database.update_trailing_sell_option_orders_market_data(api_data)


# WORKING
def monitor_trailing_sell_option_orders(runner_name: str) -> None:
	trailing_orders = database.get_all_from_table("trailing_sell_option_orders")

	for order in trailing_orders:
		logger.info(f"Monitoring trailing option order: {order}", extra={"runner": runner_name})

		if order["executed"]:
			logger.info(
				f"Trailing order #{order["order_id_pk"]} already executed. Skipping monitor.", 
				extra={"runner": runner_name}
			)
			continue

		option_market_row = database.get_single_row_from_table(
			table="trailing_sell_option_orders_market_data", 
			where_field="option_uuid_pk", 
			where_value=order["robinhood_option_uuid"]
		)
		logger.info(
			f"Fetched option market data for trailing order {order['order_id_pk']}: {option_market_row}", 
			extra={"runner": runner_name}
		)
		if option_market_row == None:
			logger.info(
				f"No market data found for option id# {order["robinhood_option_uuid"]} {order['symbol']} | {order['expiration_date']} | {order['strike']} | {order['call_or_put']}. Skipping this order.", 
				extra={"runner": runner_name}
			)
			continue
		
		if order["highest_price_since_order_placed"] == None:
			highest_price_since_order_placed = float(order["purchase_price"])
			logger.info(
				f"Setting initial highest_price_since_order_placed for order to purchase_price #{order['order_id_pk']}: purchase_price={order['purchase_price']}, highest_price_since_order_placed={highest_price_since_order_placed}", 
				extra={"runner": runner_name}
			)
		else:
			highest_price_since_order_placed = float(order["highest_price_since_order_placed"])
			logger.info(
				f"Existing highest_price_since_order_placed for order {order['order_id_pk']}: {highest_price_since_order_placed}", 
				extra={"runner": runner_name}
			)
		current_mark_price = float(option_market_row["json_data"]["mark_price"])
		logger.info(
			f"Current mark price for order {order['order_id_pk']}: {current_mark_price}", 
			extra={"runner": runner_name}
		)

		if current_mark_price > highest_price_since_order_placed:
			logger.info(
				f"New highest mark price {current_mark_price} exceeds previous highest price {highest_price_since_order_placed} for order {order['order_id_pk']}. Updating highest price.", 
				extra={"runner": runner_name}
			)
			highest_price_since_order_placed = current_mark_price
			database.set_table_field_where(
				table="trailing_sell_option_orders",
				field="highest_price_since_order_placed",
				field_value=highest_price_since_order_placed,
				where_field="order_id_pk",
				where_value=order["order_id_pk"]
			)

		percent_from_high_sell_trigger = float(order["percent_from_high_sell_trigger"])
		sell_at_specific_price = float(order["sell_at_specific_price"])

		execute_order = False
		if current_mark_price < highest_price_since_order_placed * percent_from_high_sell_trigger:
			execute_order = True
			logger.info(
				f"Current mark price {current_mark_price} is below percent threshold for order.\n"
				f"Current mark price {current_mark_price}.\n"
				f"Highest price since order placed {highest_price_since_order_placed}.\n"
				f"Percent from high sell trigger: {percent_from_high_sell_trigger}.\n"
				f"Selling: {order} {option_market_row}",
				extra={"runner": runner_name}
			)
		if current_mark_price >= sell_at_specific_price:
			execute_order = True
			logger.info(
				f"Specific price trigger met for order.\n"
				f"Specific price trigger: {sell_at_specific_price}.\n"
				f"Current mark price: {current_mark_price}.\n"
				f"Selling: {order} {option_market_row}",
				extra={"runner": runner_name}
			)

		execution_requires_trigger_order_ids = order["execute_only_after_trigger_order_ids"]
		execution_requires_bracket_sell_order_ids = order["execute_only_after_bracket_sell_order_ids"]
		execution_requires_trailing_sell_order_ids = order["execute_only_after_trailing_sell_order_ids"]
		logger.info("Checking that required previous orders have been executed.", extra={"runner": runner_name})
		executed_statuses_list = database.get_executed_status_orders(
			execution_requires_trigger_order_ids,
			execution_requires_bracket_sell_order_ids,
			execution_requires_trailing_sell_order_ids
		)
		logger.info(f"Executed statuses list: {executed_statuses_list}", extra={"runner": runner_name})
		for order_executed in executed_statuses_list:
			if order_executed == False:
				logger.info("A required previous order has not been executed. Not executing this trailing sell order yet.", extra={"runner": runner_name})
				execute_order = False

		if order["executed"] == True:
			logger.info("Order already executed. Not executing again.", extra={"runner": runner_name})
			execute_order = False

		if order["active"] == False:
			logger.info("Order is not active. Not executing.", extra={"runner": runner_name})
			execute_order = False

		execution_deactivates_trigger_order_ids = order["execution_deactivates_trigger_order_ids"]
		execution_deactivates_bracket_sell_order_ids = order["execution_deactivates_bracket_sell_order_ids"]
		execution_deactivates_trailing_sell_order_ids = order["execution_deactivates_trailing_sell_order_ids"]
		if execute_order:
			try:
				database.set_table_field_value_where(
					table="trailing_sell_option_orders", 
					field="executed", 
					field_value=True, 
					where_field="order_id_pk", 
					where_value=order["order_id_pk"]
				)
				logger.info(f"Marked trailing order #{order['order_id_pk']} as executed.", extra={"runner": runner_name})
				database.deactivate_orders(
					execution_deactivates_trigger_order_ids, 
					execution_deactivates_bracket_sell_order_ids, 
					execution_deactivates_trailing_sell_order_ids
				)
				logger.info(f"Deactivated dependent orders for trailing order #{order['order_id_pk']}", extra={"runner": runner_name})
				logger.info(f"Placing market sell for trailing order #{order['order_id_pk']}: {order}", extra={"runner": runner_name})
				orders.execute_market_sell(order, runner_name, f"Executing trailing sell order: {order}")
				logger.info(f"Executed sell for trailing order #{order['order_id_pk']}: {order}", extra={"runner": runner_name})
			except Exception as e:
				logger.exception(f"Issue selling trailing order #{order['order_id_pk']}. Exception: {e}", extra={"runner": runner_name})



def start_data_fetch_runner(runner_dict):
	logger.info(
		f"Starting data fetch runner: {runner_dict['runner_name']}.",
		extra={"runner": runner_dict["runner_name"]},
	)

	runner = DataFetchRunner(runner_dict)
	runner.write_runner_status()

	while True:
		logger.info("START RUNNER LOOP")

		runner.status = runner.get_runner_status()
		logger.info(
			f"Begin loop runner status: {runner.status}",
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
		logger.info(f"runner.status: {runner.status}")
		runner.write_runner_status()

		try:
			# Get API data
			logger.info("Attempting to fetch api_data.")
			api_data = runner.get_data()

			logger.info(
				f"Runner {runner.status['runner_name_pk']} api_data: {api_data}",
				extra={"runner": runner.status["runner_name_pk"]},
			)
		except Exception as e:
			logger.info("Issue fetching api_data.")
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

			logger.info(f"Becuase api_data fetch failed, writing failed runner status and pausing for adjusted interval: {runner.status['adjusted_interval']}")
			logger.info(f"runner.status: {runner.status}")
			runner.write_runner_status()
			time.sleep(runner.status["adjusted_interval"])
			continue

		api_data_match = None
		if len(api_data) > 0:
			logger.info(
				f"Entering verification for {runner.status['runner_name_pk']}",
				extra={"runner": runner.status["runner_name_pk"]},
			)
			print(api_data)
			if type(api_data) == list and len(api_data) >= 1:
				api_data_match = runner.verify_data(api_data[0])
			else:
				api_data_match = runner.verify_data(api_data)
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
			# Store API data
			logger.info("Attempting to store api_data.")
			runner.store_data(api_data)
			
			runner.status["current_update_success"] = True
			runner.status["previous_update_success"] = True
			runner.status["epoch_time_previous_success"] = database.get_rounded_epoch_time()
			logger.info(f"New epoch_time_previous_success: {runner.status['epoch_time_previous_success']}")
			t_f = datetime.datetime.fromtimestamp(runner.status["epoch_time_previous_success"]).strftime("%d/%m/%Y, %H:%M:%S")
			logger.info(f"Epoch converted: {t_f}")
			if runner.status["adjusted_interval"] > runner.status["default_interval"]:
				runner.status["adjusted_interval"] -= config.RUNNER_SUCCESS_ADJUSTMENT
			if runner.status["adjusted_interval"] < runner.status["default_interval"]:
				runner.status["adjusted_interval"] = runner.status["default_interval"]
			logger.info(f"runner adjusted interval after decisions: {runner.status["adjusted_interval"]}")

			logger.info(f"api_data stored. entering sleep interval: {runner.status["adjusted_interval"]}")
			
			logger.info(f"runner.status: {runner.status}")
			runner.write_runner_status()
			time.sleep(runner.status["adjusted_interval"])
			# runner.status["epoch_time_previous_success"] = database.get_rounded_epoch_time()
			# runner.write_runner_status()
			continue
		except Exception as e:
			logger.info("Issue storing api_data.")
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
			# Call the monitor function
			runner_dict["monitor_function"](runner_dict['runner_name'])

			runner.status["current_update_success"] = True
			runner.status["previous_update_success"] = True
			runner.status["epoch_time_previous_success"] = database.get_rounded_epoch_time()
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


def main(runner):
	# set up logging
	log_name = f"runner_{runner}"
	log.setup_runner_logger(log_name)

	# set logger for runner name across modules
	global logger
	logger = logging.getLogger(log_name)
	database.logger = logging.getLogger(log_name)
	orders.logger = logging.getLogger(log_name)

	# database.drop_all_tables()
	database.create_all_tables()

	r.login(config.ROBINHOOD_USERNAME, config.ROBINHOOD_PASSWORD)
	orders.robinhood_login()

	# orders.create_trigger_option_order(
	# 	active=True,
	# 	epoch_time_created_at=database.get_rounded_epoch_time(),
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

	# orders.create_trigger_option_order(
	# 	active=True,
	# 	epoch_time_created_at=database.get_rounded_epoch_time(),
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
	# 	max_mark_order_attempts=4,
	#   max_spread_order_attempts=4,
	# 	emergency_order_fill_on_failure=True,
	# 	trigger_order_uuid=str(uuid.uuid4())
	# )

	# orders.create_bracket_option_order(
	#     active=True,
    #     epoch_time_created_at=database.get_rounded_epoch_time(),
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
	# 	  max_mark_order_attempts=4,
	#     max_spread_order_attempts=4,
    #     emergency_order_fill_on_failure=True
	# )

	# orders.create_trailing_sell_option_order(
	# 	active=True, 
	# 	epoch_time_created_at=database.get_rounded_epoch_time(), 
	# 	executed=False, 
	# 	execute_only_after_trigger_order_ids=[], 
	# 	execute_only_after_bracket_sell_order_ids=[], 
	# 	execute_only_after_trailing_sell_order_ids=[], 
	# 	execution_deactivates_trigger_order_ids=[], 
	# 	execution_deactivates_bracket_sell_order_ids=[], 
	# 	execution_deactivates_trailing_sell_order_ids=[], 
	# 	quantity=1,
	# 	symbol="IWM",
	# 	call_or_put="call",
	# 	expiration_date="2026-02-02",
	# 	strike=269.0,
	# 	message_on_success="success msg",
	# 	message_on_failure="failure msg",
	# 	max_mark_order_attempts=4,
	# 	max_spread_order_attempts=4,
	# 	emergency_order_fill_on_failure=True, 
	# 	percent_from_high_sell_trigger=.90,
	# 	sell_at_specific_price=.01,
	# 	purchase_price=.02,
	# )

	runner = RUNNERS[runner]
	if runner["type"] == "data_fetch":
		start_data_fetch_runner(runner)
	if runner["type"] == "order_monitor":
		start_monitor_runner(runner)


RUNNERS = {
	"portfolio_profile": 
		{
			"runner_name": "portfolio_profile",
			"active": True,
			"get_data_function": get_data_portfolio_profile,
			"verify_data_keyset": "get_portfolio_profile",
			"store_data_function": store_data_portfolio_profile,
			"default_interval": config.PORTFOLIO_PROFILE_REFRESH_INTERVAL,
			"type": "data_fetch",
		},
	"open_option_positions": 
		{
			"runner_name": "open_option_positions",
			"active": True,
			"get_data_function": get_data_open_option_positions,
			"verify_data_keyset": "get_open_option_positions",
			"store_data_function": store_data_open_option_positions,
			"default_interval": config.OPEN_POSITIONS_REFRESH_INTERVAL,
			"type": "data_fetch",
		},
	"open_option_positions_market_data":
		{
			"runner_name": "open_option_positions_market_data",
			"active": True,
			"get_data_function": get_data_open_option_positions_market_data,
			"verify_data_keyset": "get_option_market_data_by_id",
			"store_data_function": store_data_open_option_positions_market_data,
			"default_interval": config.MARKET_DATA_REFRESH_INTERVAL,
			"type": "data_fetch",
		},
	"open_option_positions_instrument_data":
		{
			"runner_name": "open_option_positions_instrument_data",
			"active": True,
			"get_data_function": get_data_open_option_positions_instrument_data,
			"verify_data_keyset": "get_option_instrument_data_by_id",
			"store_data_function": store_data_open_option_positions_instrument_data,
			"default_interval": config.INSTRUMENT_DATA_REFRESH_INTERVAL,
			"type": "data_fetch",
		},
	# "open_broker_option_orders":
	# 	{
	# 		"runner_name": "open_broker_option_orders",
	# 		"active": True,
	# 		"get_data_function": get_data_open_broker_option_orders,
	# 		"verify_data_keyset": "get_all_open_option_orders",
	# 		"store_data_function": store_data_open_broker_option_orders,
	# 		"default_interval": config.BROKER_ORDERS_REFRESH_INTERVAL,
	# 		"type": "data_fetch",
	# 	},
	# "open_broker_option_orders_market_data":
	# 	{
	# 		"runner_name": "open_broker_option_orders_market_data",
	# 		"active": True,
	# 		"get_data_function": get_data_open_broker_option_orders_market_data,
	# 		"verify_data_keyset": "get_option_market_data_by_id",
	# 		"store_data_function": store_data_open_broker_option_orders_market_data,
	# 		"default_interval": config.MARKET_DATA_REFRESH_INTERVAL,
	# 		"type": "data_fetch",
	# 	},
	# "open_broker_option_orders_instrument_data":
	# 	{
	# 		"runner_name": "open_broker_option_orders_instrument_data",
	# 		"active": True,
	# 		"get_data_function": get_data_open_broker_option_orders_instrument_data,
	# 		"verify_data_keyset": "get_option_instrument_data_by_id",
	# 		"store_data_function": store_data_open_broker_option_orders_instrument_data,
	# 		"default_interval": config.INSTRUMENT_DATA_REFRESH_INTERVAL,
	# 		"type": "data_fetch",
	# 	},
	# {
	# 	"runner_name": "trigger_option_orders_market_data",
	# 	"active": True,
	# 	"get_data_function": get_data_trigger_option_orders_market_data,
	# 	"verify_data_keyset": "get_option_market_data_by_id",
	# 	"store_data_function": store_data_trigger_option_orders_market_data,
	# 	"default_interval": config.MARKET_DATA_REFRESH_INTERVAL,
	# 	"type": "data_fetch",
	# },
	# {
	# 	"runner_name": "bracket_sell_option_orders_market_data",
	# 	"active": True,
	# 	"get_data_function": get_data_bracket_option_orders_market_data,
	# 	"verify_data_keyset": "get_option_market_data_by_id",
	# 	"store_data_function": store_data_bracket_option_orders_market_data,
	# 	"default_interval": config.MARKET_DATA_REFRESH_INTERVAL,
	# 	"type": "data_fetch",
	# },
	# {
	# 	"runner_name": "trailing_sell_option_orders_market_data",
	# 	"active": True,
	# 	"get_data_function": get_data_trailing_sell_option_orders_market_data,
	# 	"verify_data_keyset": "get_option_market_data_by_id",
	# 	"store_data_function": store_data_trailing_sell_option_orders_market_data,
	# 	"default_interval": config.MARKET_DATA_REFRESH_INTERVAL,
	# 	"type": "data_fetch",
	# },
	# {
	# 	"runner_name": "monitor_bracket_sell_option_orders",
	# 	"active": True,
	# 	"monitor_function": monitor_bracket_option_orders,
	# 	"default_interval": 1,
	# 	"type": "order_monitor",
	# },
	# {
	# 	"runner_name": "monitor_trailing_sell_option_orders",
	# 	"active": True,
	# 	"monitor_function": monitor_trailing_sell_option_orders,
	# 	"default_interval": 1,
	# 	"type": "order_monitor",
	# },
}


if __name__ == "__main__":
	main(runner=sys.argv[1])
