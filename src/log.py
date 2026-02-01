import datetime
import json
import logging
import logging.handlers
import os
import sys
import uuid

from zoneinfo import ZoneInfo

import config


class SafeFormatter(logging.Formatter):
	def format(self, record: logging.LogRecord) -> str:
		if not hasattr(record, "runner"):
			record.runner = "unknown"
		return super().format(record)


class JSONFormatter(logging.Formatter):
	def format(self, record: logging.LogRecord) -> str:
		log_data = {
			"timestamp": self.formatTime(record),
			"process": record.process,
			"filename": record.filename,
			"lineno": record.lineno,
			"levelname": record.levelname,
			"message": record.getMessage(),
		}
		if hasattr(record, "runner"):
			log_data["runner"] = record.runner
		if record.exc_info:
			log_data["exception"] = self.formatException(record.exc_info)
		return json.dumps(log_data)


def create_log_directory() -> None:
	log_dir = f"{config.LOG_BASE_DIR}"
	try:
		os.makedirs(log_dir)
	except FileExistsError as e:
		print(f"{config.LOG_BASE_DIR} directory exists already: {e}")


def create_log_orders_directory() -> None:
	log_orders_dir = f"{config.LOG_ORDERS_DIR}"
	try:
		os.makedirs(log_orders_dir)
	except FileExistsError as e:
		print(f"{config.LOG_ORDERS_DIR} directory exists already: {e}")


def setup_runners_logger(
	log_name,
	file_logging_on=config.FILE_LOGGING,
	stdout_logging_on=config.STDOUT_LOGGING,
	jsonl_logging_on=config.JSONL_LOGGING,
):
	logger = logging.getLogger(log_name)
	logger.setLevel(eval(f"logging.{config.LOG_LEVEL}"))

	formatter = SafeFormatter(
		"%(asctime)s | p%(process)s | {%(filename)s:%(lineno)d} | %(levelname)s | runner=%(runner)s \n %(message)s\n\n"
	)

	if file_logging_on:
		log_dir = create_log_directory()
		log_file = os.path.join(log_dir, f"{log_name}.log")
		file_handler = logging.handlers.RotatingFileHandler(
			log_file, mode="a", maxBytes=1000000, backupCount=10
		)
		file_handler.setFormatter(formatter)
		logger.addHandler(file_handler)

	if jsonl_logging_on:
		log_dir = create_log_directory()
		jsonl_file = os.path.join(log_dir, f"{log_name}.jsonl")
		jsonl_handler = logging.handlers.RotatingFileHandler(
			jsonl_file, mode="a", maxBytes=1000000, backupCount=10
		)
		json_formatter = JSONFormatter()
		jsonl_handler.setFormatter(json_formatter)
		logger.addHandler(jsonl_handler)

	if stdout_logging_on:
		stream_handler = logging.StreamHandler(stream=sys.stdout)
		stream_handler.setFormatter(formatter)
		logger.addHandler(stream_handler)

	return logger

class OrderLogger():
	def __init__(self, symbol, expiration_date, strike, quantity, buy_or_sell, credit_or_debit, description):
		self.symbol = symbol
		self.expiration_date = expiration_date
		self.strike = strike
		self.quantity = quantity
		self.buy_or_sell = buy_or_sell
		self.credit_or_debit = credit_or_debit
		self.description = description
		self.unique_id = str(uuid.uuid4())
		
		self.log_file_path = os.path.join(
			config.LOG_ORDERS_DIR,
			f"order_{self.symbol}_{self.expiration_date}_{self.strike}_{self.buy_or_sell}_{self.quantity}_for_{self.credit_or_debit}_{self.unique_id}.log"
		)

		self.log(
			f"Created OrderLogger for {self.description}.\n"
			f"Log file: {self.log_file_path}\n"
			f"Details: symbol={self.symbol}, expiration_date={self.expiration_date}, strike={self.strike}, quantity={self.quantity}, buy_or_sell={self.buy_or_sell}, credit_or_debit={self.credit_or_debit}\n"
		)
		

	def log(self, message: str) -> None:
		est_timestamp = datetime.datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M:%S %Z")

		log_message = f"{est_timestamp}\n{message}\n\n"
		with open(self.log_file_path, "a") as log_file:
			log_file.write(log_message)

