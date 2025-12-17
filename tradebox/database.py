# SQL only, no http requests
import json
import os
import sqlite3
import time

import config
import log

# Logging
logger = log.get_logger(log_title="database")

DB_FILE = os.path.join(config.DATABASE_DIR, config.DATABASE_NAME)

# TABLES
# open_options_positions
# open_options_positions_market_data
# options_broker_orders
# options_broker_orders_market_data
# options_trigger_orders
# options_trigger_orders_market_data
DATABASE_TABLES = {
    "runners": {
        "runner_function_name": "TEXT PRIMARY KEY",
        "active": "INTEGER",
        "adjusted_interval": "INTEGER",
        "default_interval": "INTEGER",
        "current_update_successful": "INTEGER",
        "currently_successful": "INTEGER",
        "last_successful_update_epoch_time": "REAL",
    },
    "account": {
        "id": "TEXT",
    },
    "open_option_positions": {
        "id": "TEXT PRIMARY KEY",
        "json_data": "JSONB",
        "still_alive": "INTEGER",
        "last_update_epoch_time": "REAL",
    },
    "open_option_positions_market_data": {
        "id": "TEXT PRIMARY KEY",
        "json_data": "JSONB",
        "still_alive": "INTEGER",
        "last_update_epoch_time": "REAL",
    },
    "open_broker_option_orders": {
        "id": "TEXT PRIMARY KEY",
        "json_data": "JSONB",
        "still_alive": "INTEGER",
        "last_update_epoch_time": "REAL",
    },
}

def get_database_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    return conn

def execute_set_database_query(sql_query: str) -> bool:
    try:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute(sql_query)
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        logger.warning(f"Unexpected exception. Issue executing sql_query: {sql_query}.")
        logger.warning(f"Exception info: {e}")
        return False

def drop_runners_table() -> bool:
    sql_query = "DROP TABLE IF EXISTS runners;"
    success = execute_set_database_query(sql_query)
    return success

def populate_runners_table(runners, active=1):
    for runner_function_name, interval in runners.items():
        sql_query = f"""
            INSERT INTO runners (
            runner_function_name, 
            active, 
            adjusted_interval, 
            default_interval, 
            current_update_successful, 
            currently_successful, 
            last_successful_update_epoch_time) 
            VALUES (
            '{runner_function_name}', 
            {active}, 
            {interval}, 
            {interval}, 
            1, 
            1, 
            {time.time()});
        """
        success = execute_set_database_query(sql_query)
    return success

def get_runner_info(runner_function_name: str) -> dict | None:
    conn = get_database_connection()
    cur = conn.cursor()

    sql_query = f"SELECT * FROM runners WHERE runner_function_name='{runner_function_name}';"
    cur.execute(sql_query)
    result = cur.fetchone()

    cur.close()
    conn.close()

    if result:
        runner_info = {
            "runner_function_name": result[0],
            "active": result[1],
            "adjusted_interval": result[2],
            "default_interval": result[3],
            "current_update_successful": result[4],
            "currently_successful": result[5],
            "last_successful_update_epoch_time": result[6],
        }
        logger.info(f"{runner_function_name} results: {runner_info}. Returning runner_info.")
        return runner_info
    else:
        logger.warning(f"No runner info for {runner_function_name}. Returning None.")
        return None
    
def update_runner(runner_info):
        # "runner_function_name": "TEXT PRIMARY KEY",
        # "active": "INTEGER",
        # "adjusted_interval": "INTEGER",
        # "default_interval": "INTEGER",
        # "current_update_successful": "INTEGER",
        # "currently_successful": "INTEGER",
        # "last_successful_update_epoch_time": "REAL",
        try:
            runner_function_name = runner_info["runner_function_name"]
            active = runner_info["active"]
            adjusted_interval = runner_info["adjusted_interval"]
            default_interval = runner_info["default_interval"]
            current_update_successful = runner_info["current_update_successful"]
            currently_successful = runner_info["currently_successful"]
            last_successful_update_epoch_time = runner_info["last_successful_update_epoch_time"]

            sql_query = f"UPDATE runners SET active={active}, adjusted_interval={adjusted_interval}, default_interval={default_interval}, current_update_successful={current_update_successful}, currently_successful={currently_successful}, last_successful_update_epoch_time='{last_successful_update_epoch_time}' WHERE runner_function_name='{runner_function_name}'";

            execute_set_database_query(sql_query)

            logger.info(f"Succcessfully updated runner: {runner_function_name}")
        except Exception as e:
            logger.warning(f"Issue updating runner: {runner_function_name}")
            logger.warning(f"Exception info {e}")
    
def create_database_tables():
    for table_name, fields in DATABASE_TABLES.items():
            sql_query = f"CREATE TABLE IF NOT EXISTS {table_name} ("
            for field, field_type in fields.items():
                sql_query += f"{field} {field_type}, "
            sql_query = sql_query[:-2]
            sql_query += ");"
            execute_set_database_query(sql_query)

def delete_database():
    try:
        os.remove(DB_FILE)
    except FileNotFoundError as e:
        logger.warning(f"Issue deleting database file: {DB_FILE}")
        logger.warning(f"{e}") 

def update_open_option_position(id, json_data_string, still_alive, last_update_epoch_time):
    sql_query = f"INSERT INTO open_option_positions (id, json_data, still_alive, last_update_epoch_time) VALUES ('{id}', '{json_data_string}', {still_alive}, {last_update_epoch_time}) ON CONFLICT(id) DO UPDATE SET json_data=excluded.json_data, still_alive=excluded.still_alive, last_update_epoch_time=excluded.last_update_epoch_time;"
   
    execute_set_database_query(sql_query)

def update_open_option_positions_market_data(id, still_alive, json_data, last_update_epoch_time):
    json_data = json.dumps(json_data)
    sql_query = f"INSERT INTO open_option_positions_market_data (id, still_alive, json_data, last_update_epoch_time) VALUES ('{id}', {still_alive}, '{json_data}', {last_update_epoch_time}) ON CONFLICT(id) DO UPDATE SET still_alive=excluded.still_alive, json_data=excluded.json_data, last_update_epoch_time=excluded.last_update_epoch_time;"
    execute_set_database_query(sql_query)

def update_open_broker_option_order(id, json_data_string, still_alive, last_update_epoch_time):
    try:
        sql_query = f"INSERT INTO open_broker_option_orders (id, json_data, still_alive, last_update_epoch_time) VALUES ('{id}', '{json_data_string}', {still_alive}, {last_update_epoch_time}) ON CONFLICT(id) DO UPDATE SET json_data=excluded.json_data, still_alive=excluded.still_alive, last_update_epoch_time=excluded.last_update_epoch_time;"
        execute_set_database_query(sql_query)
        return True
    except Exception as e:
        logger.critical(f"Exception: {e}")
        return False

def delete_rows_from_table_by_value(table, field, value):
    sql_query = f"DELETE FROM {table} WHERE {field}={value}";
    execute_set_database_query(sql_query)

def set_table_field(table, field, value):
    sql_query = f"UPDATE {table} SET {field}={value};"
    execute_set_database_query(sql_query)

def get_json_field_from_table_as_list(table, field, key_name):
    conn = get_database_connection()
    cur = conn.cursor()

    sql_query = f"SELECT json_extract({field}, '$.{key_name}') as value FROM {table};"
    cur.execute(sql_query)
    results = cur.fetchall()

    basic_list_result = []
    for item in results:
        basic_list_result.append(item[0])

    cur.close()
    conn.close()

    return basic_list_result

def get_json_field_from_table(table, field, key_name):
    conn = get_database_connection()
    cur = conn.cursor()

    sql_query = f"SELECT json_extract({field}, '$.{key_name}') as value FROM {table};"
    cur.execute(sql_query)
    results = cur.fetchall()

    cur.close()
    conn.close()

    return results
