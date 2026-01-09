import logging
import os

import robin_stocks.robinhood as r

import config

logger = logging.getLogger(__name__)


def login() -> bool:
	try:
		res = r.login(config.ROBINHOOD_USERNAME, config.ROBINHOOD_PASSWORD)
		logger.info(f"Logged into Robinhood successfully: {res}")
		return True
	except Exception as e:
		logger.exception(f"Issue logging into Robinhood: {e}", stack_info=True)
		return False

def logout_and_remove_token() -> None:
	try:
		r.logout()
	except Exception as e:
		logger.exception(f"Issue logging out of Robinhood: {e}", stack_info=True)
	finally:
		home_dir = os.path.expanduser("~")
		data_dir = os.path.join(home_dir, ".tokens")
		creds_file = "robinhood.pickle"
		pickle_path = os.path.join(data_dir, creds_file)
		try:
			os.remove(pickle_path)
			logger.info("Removed Robinhood pickle file successfully")
		except FileNotFoundError:
			logger.exception("No pickle file found to remove.", stack_info=True)

	logger.info("Logged out of Robinhood successfully")

def create_trigger_option_order(
		"created_at, "
		"rh_option_uuid, "
		"execute_only_after_id, "
		"buy_sell, "
		"symbol, "
		"expiration_date, "
		"strike, "
		"call_or_put, "
		"quantity, "
		"market_or_limit, "
		"below_tick, "
		"above_tick, "
		"cutoff_price, "
		"limit_price, "
		"message_on_success, "
		"message_on_failure, "
		"max_order_attempts, "
		"execution_deactivates_order_id, "
		"active, "
		"emergency_order_fill_on_failure"
 		db_connection,
 		account_id: int,
 		option_symbol: str,
 		order_type: str,
 		strike_price: float,
 		expiration_date: str,
 		quantity: int,
 		direction: str,
 		trigger_price: float,
 		time_in_force: str,
 		extended_hours: bool,
 		status: str,
 		creation_timestamp: int,
 		last_updated_timestamp: int,
 		completed_timestamp: int,
 		failure_reason: str,
 		num_order_attempts: int,
	):
	
	r.get_option_instrument_data(option_symbol, expiration_date, strike_price, call_or_put)