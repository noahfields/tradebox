from contextlib import contextmanager
import logging
import os
import json
import psycopg2
import psycopg2.extras
import time

import config

logger = logging.getLogger(__name__)


DATABASE_TABLE_SCHEMA = {
	"runners": {
        "runner_name_pk": "VARCHAR(255) PRIMARY KEY",
        "active": "BOOLEAN",
        "adjusted_interval": "INTEGER",
        "default_interval": "INTEGER",
        "current_update_success": "BOOLEAN",
        "previous_update_success": "BOOLEAN",
        "epoch_time_previous_success": "REAL",
    },

    "open_option_positions": {
        "position_uuid_pk": "VARCHAR(255) PRIMARY KEY",
        "json_data": "JSONB",
        "still_alive": "INTEGER",
        "last_update_epoch_time": "REAL",
    },

    "open_option_positions_market_data": {
        "option_uuid_pk": "VARCHAR(255) PRIMARY KEY",
        "json_data": "JSONB",
        "still_alive": "INTEGER",
        "last_update_epoch_time": "REAL",
    },

    "open_broker_option_orders": {
        "order_uuid_pk": "VARCHAR(255) PRIMARY KEY",
        "json_data": "JSONB",
        "still_alive": "INTEGER",
        "last_update_epoch_time": "REAL",
    },

    "open_broker_option_orders_market_data": {
        "option_uuid_pk": "VARCHAR(255) PRIMARY KEY",
        "json_data": "JSONB",
        "still_alive": "INTEGER",
        "last_update_epoch_time": "REAL",
    },

    "trigger_option_orders": {
        "trigger_order_id": "SERIAL PRIMARY KEY",
        "active": "INTEGER",
        "epoch_time_created_at": "REAL",
        "executed": "INTEGER DEFAULT 0",
        "execute_only_after_id": "INTEGER",
        "execution_deactivates_order_id": "INTEGER",
        "buy_or_sell": "TEXT",
        "credit_or_debit": "TEXT",
        "symbol": "TEXT",
        "strike": "REAL",
        "call_or_put": "TEXT",
        "expiration_date": "TEXT",
        "rh_option_uuid": "TEXT",
        "market_or_limit": "TEXT",
        "limit_price": "REAL",
        "quantity": "INTEGER",
        "message_on_success": "TEXT",
        "message_on_failure": "TEXT",
        "below_tick": "REAL",
        "above_tick": "REAL",
        "cutoff_price": "REAL",
        "max_order_attempts": "INTEGER",
        "emergency_order_fill_on_failure": "INTEGER",
    },

    "trigger_option_orders_market_data": {
        "option_uuid_pk": "VARCHAR(255) PRIMARY KEY",
        "json_data": "JSONB",
        "still_alive": "INTEGER",
        "last_update_epoch_time": "REAL",
    },
}


def get_database_connection() -> psycopg2.extensions.connection:
	try:
		conn = psycopg2.connect(config.DATABASE_URI)
		conn.autocommit = False
		return conn
	except Exception as e:
		logger.exception(
			f"Error in database.get_database_connection(): {e}", 
            stack_info=True
		)


def execute_set_database_query(sql_query: str, runner_name: str = "unknown") -> bool:
    try:
        conn = get_database_connection()
        cur = conn.cursor()
        cur.execute(sql_query)
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        logger.exception(
             f"Unexpected exception. Issue executing sql_query: {sql_query}.\n", 
             stack_info=True, 
             extra={"runner": runner_name}
        )
        if 'conn' in locals():
            conn.close()
        return False


def drop_table(table: str) -> bool:
    sql_query = f"DROP TABLE IF EXISTS {table};"
    success = execute_set_database_query(sql_query)
    return success

# def get_all_runners_status() -> list:
# 	conn = get_database_connection()
# 	cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

# 	sql_query = "SELECT * FROM runners;"
# 	cur.execute(sql_query)
# 	results = cur.fetchall()

# 	runner_status_list = []
# 	for result in results:
# 		runner_info = {
# 			"runner_name": result["runner_name"],
# 			"active": result["active"],
# 			"adjusted_interval": result["adjusted_interval"],
# 			"default_interval": result["default_interval"],
# 			"current_update_successful": result["current_update_successful"],
# 			"currently_successful": result["currently_successful"],
# 			"last_successful_update_epoch_time": result["last_successful_update_epoch_time"],
# 		}
# 		runner_status_list.append(runner_info)

# 	cur.close()
# 	conn.close()

# 	return runner_status_list

def get_runner_status(runner_name_pk: str) -> dict | None:
    conn = get_database_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    sql_query = (
        f"SELECT * FROM runners WHERE runner_name_pk='{runner_name_pk}';"
    )
    cur.execute(sql_query)
    result = cur.fetchone()

    cur.close()
    conn.close()

    if result:
        runner_status = {
			"runner_name_pk": result["runner_name_pk"],
			"active": result["active"],
			"adjusted_interval": result["adjusted_interval"],
			"default_interval": result["default_interval"],
			"current_update_success": result["current_update_success"],
			"previous_update_success": result["previous_update_success"],
			"epoch_time_previous_success": result["epoch_time_previous_success"],
		}
        logger.info(f"Got runner status for {runner_name_pk}:\n{runner_status}", extra={"runner": runner_name_pk})
        return runner_status
    else:
        logger.error(f"No runner status entry for {runner_name_pk}. Returning None.", extra={"runner": runner_name_pk})
        return None


def create_all_tables():
    for table_name, columns in DATABASE_TABLE_SCHEMA.items():
        try:
            sql_query = (
                f"CREATE TABLE IF NOT EXISTS {table_name} ("
            )

            for column, data_type in columns.items():
                sql_query += f"{column} {data_type}, "

            sql_query = sql_query[:-2]
            sql_query += ");"

            execute_set_database_query(sql_query)
            logger.info(f"Database table {table_name} created.")
        except Exception as e:
            logger.exception(f"Issue creating database table {table_name}.")


def delete_all_tables():
	try:
		conn = get_database_connection()
		cur = conn.cursor()
		
		for table_name in DATABASE_TABLE_SCHEMA.keys():
			cur.execute(f"DROP TABLE IF EXISTS {table_name};")
		
		conn.commit()
		cur.close()
		conn.close()
		logger.info("Database tables deleted successfully")
	except Exception as e:
		logger.error(f"Error deleting database tables: {e}", stack_info=True)

def write_runner_status(runner_status: dict) -> None:
    try:
        sql_query = (
            "INSERT INTO runners ("
            "runner_name_pk, "
			"active, "
			"adjusted_interval, "
            "default_interval, "
			"current_update_success, "
            "previous_update_success, "
            "epoch_time_previous_success) "
			"VALUES ("
            f"\'{runner_status['runner_name_pk']}\', "
            f"{runner_status['active']}, "
            f"{runner_status['adjusted_interval']}, "
            f"{runner_status['default_interval']}, "
            f"{runner_status['current_update_success']}, "
            f"{runner_status['previous_update_success']}, "
            f"{runner_status['epoch_time_previous_success']}) "
            "ON CONFLICT(runner_name_pk) DO UPDATE SET "
            "active=excluded.active, "
            "adjusted_interval=excluded.adjusted_interval, "
            "default_interval=excluded.default_interval, "
            "current_update_success=excluded.current_update_success, "
            "previous_update_success=excluded.previous_update_success, "
            "epoch_time_previous_success=excluded.epoch_time_previous_success"
            ";"
        )
        execute_set_database_query(sql_query)
        logger.info(
            f"Wrote runner status for {runner_status['runner_name_pk']}.\nStatus details:\n{runner_status}",
            extra={"runner": runner_status["runner_name_pk"]}
        )
    except Exception as e:
        logger.exception(stack_info=True)


def update_open_option_positions(open_option_positions) -> None:
    set_table_field("open_option_positions", "still_alive", 0)

    for position in open_option_positions:
        position_uuid_pk = position["id"]
        json_data = json.dumps(position)
        last_update_epoch_time = time.time()
        still_alive = 1

        sql_query = f"INSERT INTO open_option_positions (position_uuid_pk, json_data, last_update_epoch_time, still_alive) VALUES ('{position_uuid_pk}', '{json_data}', {last_update_epoch_time}, {still_alive}) ON CONFLICT(position_uuid_pk) DO UPDATE SET json_data=excluded.json_data, last_update_epoch_time=excluded.last_update_epoch_time, still_alive=excluded.still_alive;"
        execute_set_database_query(sql_query)

    delete_rows_from_table_by_value("open_option_positions", "still_alive", 0)


def update_open_option_positions_market_data(options_market_data: list) -> None:
    set_table_field("open_option_positions_market_data", "still_alive", 0)

    for option in options_market_data:
        option_uuid_pk = option["instrument_id"]
        json_data = json.dumps(option)
        last_update_epoch_time = time.time()
        still_alive = 1
        try:
            sql_query = f"INSERT INTO open_option_positions_market_data (option_uuid_pk, json_data, last_update_epoch_time, still_alive) VALUES ('{option_uuid_pk}', '{json_data}', {last_update_epoch_time}, {still_alive}) ON CONFLICT(option_uuid_pk) DO UPDATE SET json_data=excluded.json_data, last_update_epoch_time=excluded.last_update_epoch_time, still_alive=excluded.still_alive;"
            execute_set_database_query(sql_query)
        except Exception as e:
            logger.exception(f"{e}", stack_info=True)     
        
    delete_rows_from_table_by_value("open_option_positions_market_data", "still_alive", 0)


def update_open_broker_option_orders(open_broker_orders: list) -> None:
    set_table_field("open_broker_option_orders", "still_alive", 0)

    for order in open_broker_orders:
        try:
            order_uuid_pk = order["id"]
            json_data = json.dumps(order)
            last_update_epoch_time = time.time()
            still_alive = 1
            sql_query = f"INSERT INTO open_broker_option_orders (order_uuid_pk, json_data, still_alive, last_update_epoch_time) VALUES ('{order_uuid_pk}', '{json_data}', {still_alive}, {last_update_epoch_time}) ON CONFLICT(order_uuid_pk) DO UPDATE SET json_data=excluded.json_data, still_alive=excluded.still_alive, last_update_epoch_time=excluded.last_update_epoch_time;"
            execute_set_database_query(sql_query)
        except Exception as e:
            logger.exception(f"{e}", stack_info=True)

    delete_rows_from_table_by_value("open_broker_option_orders", "still_alive", 0)


def update_open_broker_option_orders_market_data(option_market_data: list) -> None:
    set_table_field("open_broker_option_orders_market_data", "still_alive", 0)

    for option in option_market_data:
        option_uuid_pk = option["instrument_id"]
        json_data = json.dumps(option)
        last_update_epoch_time = time.time()
        still_alive = 1
        try:
            sql_query = f"INSERT INTO open_broker_option_orders_market_data (option_uuid_pk, json_data, last_update_epoch_time, still_alive) VALUES ('{option_uuid_pk}', '{json_data}', {last_update_epoch_time}, {still_alive}) ON CONFLICT(option_uuid_pk) DO UPDATE SET json_data=excluded.json_data, last_update_epoch_time=excluded.last_update_epoch_time, still_alive=excluded.still_alive;"
            execute_set_database_query(sql_query)
        except Exception as e:
            logger.exception(f"{e}", stack_info=True)

    delete_rows_from_table_by_value("open_broker_option_orders_market_data", "still_alive", 0)

def delete_rows_from_table_by_value(table, field, value) -> None:
    sql_query = f"DELETE FROM {table} WHERE {field}={value};"
    execute_set_database_query(sql_query)


def set_table_field(table: str, field: str, value) -> None:
    sql_query = f"UPDATE {table} SET {field}={value};"
    execute_set_database_query(sql_query)


def get_json_field_from_table_as_list(table, field, key_name) -> list:
	conn = get_database_connection()
	cur = conn.cursor()

	sql_query = f"SELECT {field} ->> '{key_name}' as value FROM {table};"
	cur.execute(sql_query)
	results = cur.fetchall()

	basic_list_result = []
	for item in results:
		basic_list_result.append(item[0])

	cur.close()
	conn.close()

	return basic_list_result


def get_json_field_from_table(table: str, field: str, key_name: str) -> list:
	conn = get_database_connection()
	cur = conn.cursor()

	sql_query = f"SELECT {field} -> '{key_name}' as value FROM {table};"
	cur.execute(sql_query)
	results = cur.fetchall()

	cur.close()
	conn.close()

	return results

def insert_trigger_order(
		active: int,
		created_at: str,
		executed: int,
		execute_only_after_id: int,
		execution_deactivates_order_id: int,
		buy_or_sell: str,
		symbol: str,
		strike: float,
		call_put: str,
		expiration_date: str,
		rh_option_uuid: str,
		market_or_limit: str,
		limit_price: float,
		quantity: int,
		message_on_success: str,
		message_on_failure: str,
		below_tick: float,
		above_tick: float,
		cutoff_price: float,
		max_order_attempts: int,
		emergency_order_fill_on_failure: int
	):
	
	sql_query = (
		"INSERT INTO trigger_option_orders("
		"created_at, "
		"rh_option_uuid, "
		"execute_only_after_id, "
		"buy_sell, "
		"symbol, "
		"expiration_date, "
		"strike, "
		"call_or_put, "
		"quantity, "
		"market_or_limit, "
		"below_tick, "
		"above_tick, "
		"cutoff_price, "
		"limit_price, "
		"message_on_success, "
		"message_on_failure, "
		"max_order_attempts, "
		"execution_deactivates_order_id, "
		"active, "
		"emergency_order_fill_on_failure"
		") "
		"VALUES ("
		f"{created_at}, "
		f"{rh_option_uuid}, "
		f"{execute_only_after_id}, "
		f"{buy_or_sell}, "
		f"{symbol}, "
		f"{expiration_date}, "
		f"{strike}, "
		f"{call_put}, "
		f"{quantity}, "
		f"{market_or_limit}, "
		f"{below_tick}, "
		f"{above_tick}, "
		f"{cutoff_price}, "
		f"{limit_price}, "
		f"{message_on_success}, "
		f"{message_on_failure}, "
		f"{max_order_attempts}, "
		f"{execution_deactivates_order_id}, "
		f"{active}, "
		f"{emergency_order_fill_on_failure}, "
	)

	result = execute_set_database_query(sql_query)
	return result