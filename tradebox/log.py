import datetime
import logging
import os
import sys

import config

def get_logger(log_title, file_logging_on=config.FILE_LOGGING, stdout_logging_on=config.STDOUT_LOGGING):
    date_prefix = datetime.datetime.now().strftime(("%Y.%m.%d"))
    log_file = f"{date_prefix} {log_title}.log"

    # Logging
    logger = logging.getLogger(__name__)
    logger.setLevel(eval(f"logging.{config.LOG_LEVEL}"))

    # Format
    formatter = logging.Formatter('%(asctime)s - p%(process)s - {%(pathname)s:%(lineno)d} - %(levelname)s \n %(message)s\n\n')

    # Log to file
    if file_logging_on:
        LOG_FILEPATH = os.path.join(config.LOG_DIR, log_file)
        file_handler = logging.FileHandler(LOG_FILEPATH)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Log to stdout
    if stdout_logging_on:
        stream_handler = logging.StreamHandler(stream=sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logger