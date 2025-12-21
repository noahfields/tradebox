from concurrent.futures import ThreadPoolExecutor
import time

import config
import database
import log
import robinhood_api

import robin_stocks.robinhood as r

# Logging
logger = log.get_logger(log_title="runners")

# Runner table
runners = {
	"runner_update_open_option_positions": config.OPEN_POSITIONS_REFRESH_INTERVAL,
	"runner_update_open_option_positions_market_data": config.MARKET_DATA_REFRESH_INTERVAL,
	"runner_update_open_broker_option_orders": config.BROKER_ORDERS_REFRESH_INTERVAL,
	"runner_update_open_broker_option_orders_market_data": config.MARKET_DATA_REFRESH_INTERVAL,
	# "runner_update_trigger_option_orders_market_data": config.MARKET_DATA_REFRESH_INTERVAL,
}


# Runner functions
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


# Loops each runner function
def loop_runner(runner_function_name):
	while True:
		logger.info(f"Starting refresh loop: {runner_function_name}")

		runner_info = database.get_runner_info(runner_function_name)
		updated_runner_info = runner_info.copy()
		logger.info(f"Successfully received runner_info: {runner_info}")

		# Skip API request if runner is not active
		if not runner_info["active"]:
			logger.info(f"Runner {runner_function_name} is not active.)")

			updated_runner_info["current_update_successful"] = 0
			updated_runner_info["currently_successful"] = 0
			database.update_runner(updated_runner_info)
			logger.info(
				f"Saved updated_runner_info for {runner_function_name}: {updated_runner_info}"
			)

			time.sleep(updated_runner_info["adjusted_interval"])
			logger.info(
				f"Runner not active. Concluded interval pause for {runner_function_name}."
			)
			continue

		# Mark run for failure (it might succeed later)
		updated_runner_info["current_update_successful"] = 0
		database.update_runner(updated_runner_info)
		logger.info(
			f"Marked for failure: {runner_function_name}, current_update_successful set to 0"
		)

		# Make API request
		success = eval(f"{runner_function_name}()")

		if success:
			# Reduce adjusted interval by 1 second if above default
			if (
				updated_runner_info["adjusted_interval"]
				> updated_runner_info["default_interval"]
			):
				updated_runner_info["adjusted_interval"] = (
					updated_runner_info["adjusted_interval"] - 1
				)

			# Last run succeeded
			updated_runner_info["current_update_successful"] = 1
			# Currently successful
			updated_runner_info["currently_succesful"] = 1
			# Time of last successful update
			updated_runner_info["last_successful_update_epoch_time"] = (
				time.time()
			)

			# Update runner entry
			database.update_runner(updated_runner_info)
			logger.info(
				f"Runner ({runner_function_name}) successfully updated."
			)

			# Pause for interval
			time.sleep(updated_runner_info["adjusted_interval"])
			logger.info(
				f"Runner paused for {updated_runner_info['adjusted_interval']}"
			)
		else:
			logger.info(
				f"Changing adjusted_intveral from {updated_runner_info['adjusted_interval']} to {runner_info['adjusted_interval'] + 1}"
			)
			updated_runner_info["adjusted_interval"] = (
				runner_info["adjusted_interval"] + 1
			)

			# Disallow runners from pausing for more than 60 seconds
			if (
				updated_runner_info["adjusted_interval"]
				>= config.MAXIMUM_INTERVAL
			):
				updated_runner_info["adjusted_interval"] = (
					config.MAXIMUM_INTERVAL
				)
			logger.info(
				f"Final decision on adjusted_interval: {updated_runner_info['adjusted_interval']} seconds"
			)

			# Set success statuses to failure
			updated_runner_info["current_update_successful"] = 0
			updated_runner_info["currently_successful"] = 0

			# Update runner
			database.update_runner(updated_runner_info)
			logger.info(
				f"Successfully updated {runner_function_name} as failure."
			)

			# Pause for 2x interval to avoid API timeout
			time.sleep(updated_runner_info["adjusted_interval"] * 2)
			logger.info(
				f"Paused 2x adjusted_interval for: {updated_runner_info['adjusted_interval'] * 2}"
			)


if __name__ == "__main__":
	r.login(config.ROBINHOOD_USERNAME, config.ROBINHOOD_PASSWORD)
	database.delete_database()
	database.create_database_tables()
	database.populate_runners_table(runners, active=1)

	max_workers = len(runners) * 2
	with ThreadPoolExecutor(max_workers=max_workers) as runner_threads:
		logger.info("Starting runners")
		for runner_function_name in runners.keys():
			print(runner_function_name)
			logger.error(f"Starting runner: {runner_function_name}")
			runner_threads.submit(loop_runner, runner_function_name)
