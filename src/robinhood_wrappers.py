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