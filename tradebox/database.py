# SQL only, no http requests
import json
import os
import sqlite3

import config as config

DB_FILEPATH = os.path.join(config.DATABASE_DIR, config.DATABASE_NAME)

# TABLES
# open_options_positions
# open_options_positions_market_data
# options_broker_orders
# options_broker_orders_market_data
# options_trigger_orders
# options_trigger_orders_market_data
DATABASE_TABLES = {
    "runners": {
        "runner_name": "TEXT PRIMARY KEY",
        "interval": "INTEGER",
        "last_update_successful": "INTEGER",
        "last_update_epoch_time": "REAL",
        "currently_succesful": "INTEGER",
        "valid_slop_time_seconds": "INTEGER",
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
}

def get_database_connection():
    conn = sqlite3.connect(DB_FILEPATH)
    return conn

def execute_database_query(sql_query):
    conn = sqlite3.connect(DB_FILEPATH)
    cur = conn.cursor()
    cur.execute(sql_query)
    conn.commit()
    cur.close()
    conn.close()

def drop_runners_table():
    sql_query = "DROP TABLE IF EXISTS runners;"
    execute_database_query(sql_query)

def populate_runners_table(runners):
    for runner_name, interval in runners.items():
        sql_query = f"INSERT INTO runners (runner_name, interval, valid_slop_time_seconds) VALUES ('{runner_name}', {interval}, {interval + 2});"
        execute_database_query(sql_query)

def get_runner_info(runner_name):
    conn = get_database_connection()
    cur = conn.cursor()

    sql_query = f"SELECT * FROM runners WHERE runner_name='{runner_name}';"
    cur.execute(sql_query)
    result = cur.fetchone()

    cur.close()
    conn.close()

    if result:
        runner_info = {
            "runner_name": result[0],
            "interval": result[1],
            "last_update_successful": result[2],
            "last_update_epoch_time": result[3],
            "currently_succesful": result[4],
            "valid_slop_time_seconds": result[5],
        }
        return runner_info
    else:
        return None

def create_database_tables():
    for table_name, fields in DATABASE_TABLES.items():
            sql_query = f"CREATE TABLE IF NOT EXISTS {table_name} ("
            for field, field_type in fields.items():
                sql_query += f"{field} {field_type}, "
            sql_query = sql_query[:-2]
            sql_query += ");"
            execute_database_query(sql_query)

def delete_database():
    os.drop(DB_FILEPATH)

def update_open_option_position(id, json_data, still_alive=1):
    json_data = json.dumps(json_data)
    still_alive = still_alive

    sql_query = f"INSERT INTO open_option_positions (id, json_data, still_alive) VALUES ('{id}', '{json_data}', {still_alive}) ON CONFLICT(id) DO UPDATE SET json_data=excluded.json_data, still_alive=excluded.still_alive;"
   
    execute_database_query(sql_query)

def update_open_option_positions_market_data(id, json_data):
    json_data = json.dumps(json_data)
    still_alive = 1
    sql_query = f"INSERT INTO open_option_positions_market_data (id, still_alive, json_data) VALUES ('{id}', {still_alive}, '{json_data}') ON CONFLICT(id) DO UPDATE SET still_alive=excluded.still_alive, json_data=excluded.json_data;"
    execute_database_query(sql_query)

def delete_rows_from_table_by_value(table, field, value):
    sql_query = f"DELETE FROM {table} WHERE {field}={value}";
    execute_database_query(sql_query)

def set_table_field(table, field, value):
    sql_query = f"UPDATE {table} SET {field}={value};"
    execute_database_query(sql_query)

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
