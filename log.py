import datetime
import os

try:
    os.mkdir('logs')
except:
    pass


def append(message):
    log_filename = f'logs/log-{datetime.datetime.now().strftime("%Y-%m-%d")}.txt'
    log_file = open(log_filename, "a")
    log_file.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))
    log_file.write("\n")
    log_file.write(message)
    log_file.write("\n\n")
