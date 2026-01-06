from concurrent.futures import ThreadPoolExecutor
import logging
import time

import robin_stocks.robinhood as r

import config
import database
import log
import robinhood_api

logger = log.setup_logger("runners")

RUNNERS = {
	"runner_update_open_option_positions": config.OPEN_POSITIONS_REFRESH_INTERVAL,
	"runner_update_open_option_positions_market_data": config.MARKET_DATA_REFRESH_INTERVAL,
	# "runner_update_open_broker_option_orders": config.BROKER_ORDERS_REFRESH_INTERVAL,
	# "runner_update_open_broker_option_orders_market_data": config.MARKET_DATA_REFRESH_INTERVAL,
	# "runner_update_trigger_option_orders_market_data": config.MARKET_DATA_REFRESH_INTERVAL,
}


def runner_update_open_option_positions():
	success = robinhood_api.update_open_option_positions()
	return success


def runner_update_open_option_positions_market_data():
	success = robinhood_api.update_open_option_positions_market_data()
	return success


def runner_update_open_broker_option_orders():
	success = robinhood_api.update_open_broker_option_orders()
	return success


def runner_update_open_broker_option_orders_market_data():
	success = robinhood_api.update_open_broker_option_orders_market_data()
	return success


# def runner_update_trigger_option_orders_market_data():
# 	return True


def execute_runner(runner_name):
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


def main():
	database.logger = logging.getLogger("runners")
	robinhood_api.logger = logging.getLogger("runners")

	r.login(config.ROBINHOOD_USERNAME, config.ROBINHOOD_PASSWORD)

	database.delete_all_tables()
	database.create_all_tables()

	database.populate_runners_table(RUNNERS, active=1)

	max_workers = len(RUNNERS)
	with ThreadPoolExecutor(max_workers=max_workers) as runner_threads:
		logger.info("Starting runners in runners.main().")
		for runner_name in RUNNERS.keys():
			logger.info(f"Submitting first run for execute_runner({runner_name})")
			runner_threads.submit(execute_runner, runner_name)


if __name__ == "__main__":
	main()
