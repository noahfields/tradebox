from contextlib import contextmanager
import logging
import os
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
        "last_successful_update_epoch_time": "REAL",
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

    "open_broker_option_orders_market_data": {
        "id": "TEXT PRIMARY KEY",
        "json_data": "JSONB",
        "still_alive": "INTEGER",
        "last_update_epoch_time": "REAL",
    },

    "trigger_option_orders": {
        "trigger_order_id": "SERIAL PRIMARY KEY",
        "active": "INTEGER",
        "created_at": "TEXT",
        "executed": "INTEGER DEFAULT 0",
        "execute_only_after_id": "INTEGER",
        "execution_deactivates_order_id": "INTEGER",
        "buy_sell": "TEXT",
        "symbol": "TEXT",
        "strike": "REAL",
        "call_put": "TEXT",
        "expiration_date": "TEXT",
        "rh_option_uuid": "TEXT",
        "market_limit": "TEXT",
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
        "id": "TEXT PRIMARY KEY",
        "json_data": "JSONB",
        "still_alive": "INTEGER",
        "last_update_epoch_time": "REAL",
    },
}


def get_database_connection() -> psycopg2.extensions.connection:
	try:
		conn = psycopg2.connect(config.DATABASE_URL)
		conn.autocommit = False
		return conn
	except Exception as e:
		logger.critical(
			f"Error in database.get_database_connection(): {e}"
		)


def execute_set_database_query(sql_query: str) -> bool:
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
			f"Unexpected exception. Issue executing sql_query: {sql_query}.\n"
		)
		return False


def drop_table(table: str) -> bool:
    sql_query = f"DROP TABLE IF EXISTS {table};"
    success = execute_set_database_query(sql_query)
    return success


def populate_runners_table(runners: dict, active: int = 1) -> bool:
    for runner_name_pk, default_interval in runners.items():
        adjusted_interval = default_interval
        current_update_success = 1
        previous_update_success = 1
        last_successful_update_epoch_time = 0
        sql_query = (
            "INSERT INTO runners ("
            "runner_name_pk, "
            "active, "
            "adjusted_interval, "
            "default_interval, "
            "current_update_success, "
            "previous_update_success, "
            "last_successful_update_epoch_time) "
            "VALUES ("
            f"'{runner_name_pk}', "
            f"{active}, "
            f"{adjusted_interval}, "
            f"{default_interval}, "
            f"{current_update_success}, "
            f"{previous_update_success}, "
            f"{last_successful_update_epoch_time}"
            ");"
        )
        success = execute_set_database_query(sql_query)
        logger.info(f"Populated runners table with {runner_name_pk}")
    return success

def get_all_runners_status() -> list:
	conn = get_database_connection()
	cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

	sql_query = "SELECT * FROM runners;"
	cur.execute(sql_query)
	results = cur.fetchall()

	runner_status_list = []
	for result in results:
		runner_info = {
			"runner_name": result["runner_name"],
			"active": result["active"],
			"adjusted_interval": result["adjusted_interval"],
			"default_interval": result["default_interval"],
			"current_update_successful": result["current_update_successful"],
			"currently_successful": result["currently_successful"],
			"last_successful_update_epoch_time": result["last_successful_update_epoch_time"],
		}
		runner_status_list.append(runner_info)

	cur.close()
	conn.close()

	return runner_status_list

def get_runner_info(runner_name_pk: str) -> dict | None:
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
		runner_info = {
			"runner_name_pk": result["runner_name_pk"],
			"active": result["active"],
			"adjusted_interval": result["adjusted_interval"],
			"default_interval": result["default_interval"],
			"current_update_success": result["current_update_success"],
			"last_update_success": result["last_update_success"],
			"last_successful_update_epoch_time": result["last_successful_update_epoch_time"],
		}
		logger.debug(
			f"get_runner_info({runner_name_pk}) results:\n {runner_info}. Returning runner_info."
		)
		return runner_info
	else:
		logger.error(f"No runner info for {runner_name_pk}. Returning None.")
		return None

def update_runner(runner_info) -> None:
    try:
        runner_name_pk = runner_info["runner_name_pk"]
        active = runner_info["active"]
        adjusted_interval = runner_info["adjusted_interval"]
        default_interval = runner_info["default_interval"]
        current_update_success = runner_info["current_update_success"]
        last_update_success = runner_info["last_update_success"]
        last_successful_update_epoch_time = runner_info["last_successful_update_epoch_time"]

        sql_query = f"UPDATE runners SET active={active}, adjusted_interval={adjusted_interval}, default_interval={default_interval}, current_update_success={current_update_success}, last_update_success={last_update_success}, last_successful_update_epoch_time='{last_successful_update_epoch_time}' WHERE runner_name_pk='{runner_name_pk}';"

        execute_set_database_query(sql_query)

        logger.debug(f"Succcessfully updated runner: {runner_name}")
    except Exception as e:
        logger.warning(f"Issue updating runner: {runner_name}")
        logger.warning(f"Exception info {e}")


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
		logger.error(f"Error deleting database tables: {e}")


def update_open_option_position(
    id: str, 
    json_data: str, 
    last_update_epoch_time: float, 
    still_alive: int = 1
    ) -> bool:
    try:
        sql_query = f"INSERT INTO open_option_positions (id, json_data, last_update_epoch_time, still_alive) VALUES ('{id}', '{json_data}', {last_update_epoch_time}, {still_alive}) ON CONFLICT(id) DO UPDATE SET json_data=excluded.json_data, last_update_epoch_time=excluded.last_update_epoch_time, still_alive=excluded.still_alive;"

        execute_set_database_query(sql_query)
        return True
    except Exception as e:
        logger.critical(f"Exception: {e}")
        return False     


def update_open_option_positions_market_data(
    id: str, 
    json_data: str, 
    last_update_epoch_time: float, 
    still_alive: int = 1
    ) -> bool:
    try:
        sql_query = f"INSERT INTO open_option_positions_market_data (id, json_data, last_update_epoch_time, still_alive) VALUES ('{id}', '{json_data}', {last_update_epoch_time}, {still_alive}) ON CONFLICT(id) DO UPDATE SET json_data=excluded.json_data, last_update_epoch_time=excluded.last_update_epoch_time, still_alive=excluded.still_alive;"
        execute_set_database_query(sql_query)
        return True
    except Exception as e:
        logger.critical(f"Exception: {e}")
        return False        


def update_open_broker_option_order(
    order_id: str, 
    json_data: str, 
    last_update_epoch_time: float, 
    still_alive:int = 1
    ) -> bool:
    try:
        sql_query = f"INSERT INTO open_broker_option_orders (id, json_data, still_alive, last_update_epoch_time) VALUES ('{order_id}', '{json_data}', {still_alive}, {last_update_epoch_time}) ON CONFLICT(id) DO UPDATE SET json_data=excluded.json_data, still_alive=excluded.still_alive, last_update_epoch_time=excluded.last_update_epoch_time;"
        execute_set_database_query(sql_query)
        return True
    except Exception as e:
        logger.critical(f"Exception: {e}")
        return False


def update_open_broker_option_orders_market_data(
    option_id: str, 
    json_data: str, 
    last_update_epoch_time: float, 
    still_alive: int = 1
    ) -> bool:
    try:
        sql_query = f"INSERT INTO open_broker_option_orders_market_data (id, json_data, last_update_epoch_time, still_alive) VALUES ('{option_id}', '{json_data}', {last_update_epoch_time}, {still_alive}) ON CONFLICT(id) DO UPDATE SET json_data=excluded.json_data, last_update_epoch_time=excluded.last_update_epoch_time, still_alive=excluded.still_alive;"
        execute_set_database_query(sql_query)
        return True
    except Exception as e:
        logger.critical(f"Exception: {e}")
        return False


def delete_rows_from_table_by_value(table, field, value):
    sql_query = f"DELETE FROM {table} WHERE {field}={value};"
    success = execute_set_database_query(sql_query)
    return success


def set_table_field(table: str, field: str, value) -> bool:
    sql_query = f"UPDATE {table} SET {field}={value};"
    success = execute_set_database_query(sql_query)
    return success


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
		"call_put, "
		"quantity, "
		"market_limit, "
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