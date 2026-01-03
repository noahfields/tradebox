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
	"runner_update_open_broker_option_orders": config.BROKER_ORDERS_REFRESH_INTERVAL,
	"runner_update_open_broker_option_orders_market_data": config.MARKET_DATA_REFRESH_INTERVAL,
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


def runner_update_trigger_option_orders_market_data():
	return True


def loop_runner(runner_name):
	while True:
		logger.debug(f"Starting refresh loop for {runner_name}.")

		runner_info = database.get_runner_info(runner_name)
		updated_runner_info = runner_info.copy()

		logger.debug(f"Successfully received {runner_name} runner_info: {runner_info}")

		if not runner_info["active"]:
			logger.debug(f"Runner {runner_name} is not active.")

			updated_runner_info["current_update_successful"] = 0
			updated_runner_info["currently_successful"] = 0
			database.update_runner(updated_runner_info)
			logger.debug(
				f"Saved updated_runner_info for {runner_name}: {updated_runner_info}"
			)

			time.sleep(updated_runner_info["adjusted_interval"])
			logger.debug(
				f"Runner {runner_name} is not active. Concluded interval pause for {runner_name}."
			)
			continue

		updated_runner_info["current_update_successful"] = 0
		database.update_runner(updated_runner_info)
		logger.debug(
			f"Marked {runner_name} for failure: current_update_successful set to 0"
		)

		success = eval(f"{runner_name}()")

		if success:
			if (
				updated_runner_info["adjusted_interval"]
				> updated_runner_info["default_interval"]
			):
				updated_runner_info["adjusted_interval"] = (
					updated_runner_info["adjusted_interval"] - 1
				)

			updated_runner_info["current_update_successful"] = 1
			updated_runner_info["currently_succesful"] = 1
			updated_runner_info["last_successful_update_epoch_time"] = (
				time.time()
			)

			database.update_runner(updated_runner_info)
			logger.debug(
				f"Runner ({runner_name}) successfully updated."
			)

			time.sleep(updated_runner_info["adjusted_interval"])
			logger.debug(
				f"Runner paused for {updated_runner_info['adjusted_interval']}"
			)
		else:
			logger.debug(
				f"Changing adjusted_intveral from {updated_runner_info['adjusted_interval']} to {runner_info['adjusted_interval'] + 1}"
			)
			updated_runner_info["adjusted_interval"] = (
				runner_info["adjusted_interval"] + 1
			)

			if (
				updated_runner_info["adjusted_interval"]
				>= config.MAXIMUM_INTERVAL
			):
				updated_runner_info["adjusted_interval"] = (
					config.MAXIMUM_INTERVAL
				)
			logger.debug(
				f"Final decision on adjusted_interval: {updated_runner_info['adjusted_interval']} seconds"
			)

			# Set success statuses to failure
			updated_runner_info["current_update_successful"] = 0
			updated_runner_info["currently_successful"] = 0

			# Update runner
			database.update_runner(updated_runner_info)
			logger.debug(
				f"Successfully updated {runner_name} as failure."
			)

			# Pause for 2x interval to avoid API timeout
			time.sleep(updated_runner_info["adjusted_interval"] * 2)
			logger.debug(
				f"Paused 2x adjusted_interval for: {updated_runner_info['adjusted_interval'] * 2}"
			)


def main():
	database.logger = logging.getLogger("runners")
	robinhood_api.logger = logging.getLogger("runners")

	r.login(config.ROBINHOOD_USERNAME, config.ROBINHOOD_PASSWORD)

	database.delete_database()
	database.create_database_tables()
	database.populate_runners_table(RUNNERS, active=1)

	max_workers = len(RUNNERS) * 2
	with ThreadPoolExecutor(max_workers=max_workers) as runner_threads:
		logger.debug("Starting runners.")
		for runner_name in RUNNERS.keys():
			logger.debug(f"Starting runner: {runner_name}")
			runner_threads.submit(loop_runner, runner_name)


if __name__ == "__main__":
	main()
