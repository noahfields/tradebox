# SQL only, no http requests
import json
import os
import sqlite3

import config

DB_FILEPATH = os.path.join(config.DATABASE_DIR, config.DATABASE_NAME)

# TABLES
# open_options_positions
# open_options_positions_market_data
# options_broker_orders
# options_broker_orders_market_data
# options_trigger_orders
# options_trigger_orders_market_data
DATABASE_TABLES = {
    "open_option_positions": {
        "id": "TEXT PRIMARY KEY",
        "still_alive": "INTEGER",
        "json_data": "JSONB",
    },
    "open_option_positions_market_data": {
        "id": "TEXT PRIMARY KEY",
        "still_alive": "INTEGER",
        "json_data": "JSONB",
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

def update_open_option_position(id, json_data):
    json_data = json.dumps(json_data)
    still_alive = 1
    sql_query = f"INSERT INTO open_option_positions (id, still_alive, json_data) VALUES ('{id}', {still_alive}, '{json_data}') ON CONFLICT(id) DO UPDATE SET still_alive=excluded.still_alive, json_data=excluded.json_data;"
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
