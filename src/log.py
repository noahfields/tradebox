import logging
import logging.handlers
import os
import sys

import config
import globals


def create_log_directory():
	log_dir = f"{globals.REPO_DIR}/logs"
	try:
		os.makedirs(log_dir)
		return log_dir
	except FileExistsError as e:
		print(f"log directory exists already: {e}")
		return log_dir
	except Exception as e:
		print(f"Unexpected exception: {e}")


def setup_logger(
	log_name,
	file_logging_on=config.FILE_LOGGING,
	stdout_logging_on=config.STDOUT_LOGGING,
):
	logger = logging.getLogger(log_name)
	logger.setLevel(eval(f"logging.{config.LOG_LEVEL}"))

	formatter = logging.Formatter(
		"%(asctime)s | p%(process)s | {%(filename)s:%(lineno)d} | %(levelname)s \n %(message)s\n\n"
	)

	if file_logging_on:
		log_dir = create_log_directory()
		log_file = os.path.join(log_dir, f"{log_name}.log")
		file_handler = logging.handlers.RotatingFileHandler(
			log_file, mode="a", maxBytes=1000000, backupCount=10
		)
		file_handler.setFormatter(formatter)
		logger.addHandler(file_handler)

	if stdout_logging_on:
		stream_handler = logging.StreamHandler(stream=sys.stdout)
		stream_handler.setFormatter(formatter)
		logger.addHandler(stream_handler)

	return logger
