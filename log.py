"""Provides server-side logging for Tradebox."""
import datetime
import os

import config

LOG_DIR = os.path.join(config.LOG_PARENT_DIR, config.LOG_DIR_NAME)
try:
    os.makedirs(LOG_DIR)
except FileExistsError:
    pass


def append(message: str) -> None:
    log_filename = f'log-{datetime.datetime.now().strftime("%Y-%m-%d")}.txt'
    log_file_path = os.path.join(LOG_DIR, log_filename)

    with open(log_file_path, mode='a', encoding='utf-8') as log_file:
        log_file.write(datetime.datetime.now().strftime(
            '%Y-%m-%d %H:%M:%S.%f'))
        log_file.write('\n')
        log_file.write(message)
        log_file.write('\n\n')
