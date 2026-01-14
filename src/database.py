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
        "still_alive": "BOOLEAN",
        "last_update_epoch_time": "REAL",
        "local_id": "SMALLSERIAL",
    },

    "open_option_positions_market_data": {
        "option_uuid_pk": "VARCHAR(255) PRIMARY KEY",
        "json_data": "JSONB",
        "still_alive": "BOOLEAN",
        "last_update_epoch_time": "REAL",
    },

    "open_broker_option_orders": {
        "order_uuid_pk": "VARCHAR(255) PRIMARY KEY",
        "json_data": "JSONB",
        "still_alive": "BOOLEAN",
        "last_update_epoch_time": "REAL",
        "local_id": "SMALLSERIAL",
    },

    "open_broker_option_orders_market_data": {
        "option_uuid_pk": "VARCHAR(255) PRIMARY KEY",
        "json_data": "JSONB",
        "still_alive": "BOOLEAN",
        "last_update_epoch_time": "REAL",
    },

    "trigger_option_orders": {
        "order_id_pk": "SMALLSERIAL PRIMARY KEY",
        "active": "BOOLEAN",
        "epoch_time_created_at": "REAL",
        "executed": "BOOLEAN DEFAULT FALSE",
        "execute_only_after_trigger_order_ids": "INTEGER[]",
        "execute_only_after_bracket_order_ids": "INTEGER[]",
        "execute_only_after_trailing_order_ids": "INTEGER[]",
        "execution_deactivates_trigger_order_ids": "INTEGER[]",
        "execution_deactivates_bracket_order_ids": "INTEGER[]",
        "execution_deactivates_trailing_order_ids": "INTEGER[]",
        "buy_or_sell": "TEXT",
        "credit_or_debit": "TEXT",
        "symbol": "TEXT",
        "strike": "REAL",
        "call_or_put": "TEXT",
        "expiration_date": "TEXT",
        "rh_option_uuid": "TEXT",
        "quantity": "INTEGER",
        "message_on_success": "TEXT",
        "message_on_failure": "TEXT",
        "below_tick": "REAL",
        "above_tick": "REAL",
        "cutoff_price": "REAL",
        "max_order_attempts": "INTEGER",
        "emergency_order_fill_on_failure": "BOOLEAN",
        "trigger_order_uuid": "UUID",
    },

    "trigger_option_orders_market_data": {
        "option_uuid_pk": "VARCHAR(255) PRIMARY KEY",
        "json_data": "JSONB",
        "still_alive": "BOOLEAN",
        "last_update_epoch_time": "REAL",
    },

    "bracket_option_orders": {
        "order_id_pk": "SMALLSERIAL PRIMARY KEY",
        "active": "BOOLEAN",
        "epoch_time_created_at": "REAL",
        "executed": "BOOLEAN DEFAULT FALSE",
        "execute_only_after_trigger_order_ids": "INTEGER[]",
        "execute_only_after_bracket_order_ids": "INTEGER[]",
        "execute_only_after_trailing_order_ids": "INTEGER[]",
        "execution_deactivates_trigger_order_ids": "INTEGER[]",
        "execution_deactivates_bracket_order_ids": "INTEGER[]",
        "execution_deactivates_trailing_order_ids": "INTEGER[]",
        "buy_or_sell": "TEXT",
        "credit_or_debit": "TEXT",
        "symbol": "TEXT",
        "strike": "REAL",
        "call_or_put": "TEXT",
        "expiration_date": "TEXT",
        "rh_option_uuid": "TEXT",
        "quantity": "INTEGER",
        "high_sell_mark_price": "REAL",
        "low_sell_mark_price": "REAL",
        "message_on_success": "TEXT",
        "message_on_failure": "TEXT",
        "below_tick": "REAL",
        "above_tick": "REAL",
        "cutoff_price": "REAL",
        "max_order_attempts": "INTEGER",
        "emergency_order_fill_on_failure": "BOOLEAN", 
    },

    "bracket_option_orders_market_data": {
        "option_uuid_pk": "VARCHAR(255) PRIMARY KEY",
        "json_data": "JSONB",
        "still_alive": "BOOLEAN",
        "last_update_epoch_time": "REAL",
    },

    "trailing_option_orders": {
        "order_id_pk": "SMALLSERIAL PRIMARY KEY",
        "active": "BOOLEAN",
        "epoch_time_created_at": "REAL",
        "executed": "BOOLEAN DEFAULT FALSE",
        "execute_only_after_trigger_order_ids": "INTEGER[]",
        "execute_only_after_bracket_order_ids": "INTEGER[]",
        "execute_only_after_trailing_order_ids": "INTEGER[]",
        "execution_deactivates_trigger_order_ids": "INTEGER[]",
        "execution_deactivates_bracket_order_ids": "INTEGER[]",
        "execution_deactivates_trailing_order_ids": "INTEGER[]",
        "buy_or_sell": "TEXT",
        "credit_or_debit": "TEXT",
        "symbol": "TEXT",
        "strike": "REAL",
        "call_or_put": "TEXT",
        "expiration_date": "TEXT",
        "rh_option_uuid": "TEXT",
        "quantity": "INTEGER",
        "message_on_success": "TEXT",
        "message_on_failure": "TEXT",
        "below_tick": "REAL",
        "above_tick": "REAL",
        "cutoff_price": "REAL",
        "max_order_attempts": "INTEGER",
        "emergency_order_fill_on_failure": "BOOLEAN", 
        "percent_from_high_sell_trigger": "REAL",
        "sell_at_specific_price": "REAL",
        "highest_price_since_order_placed": "REAL",
        "cost_basis": "REAL",
    },

    "trailing_option_orders_market_data": {
        "option_uuid_pk": "VARCHAR(255) PRIMARY KEY",
        "json_data": "JSONB",
        "still_alive": "BOOLEAN",
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


def drop_table(table: str) -> None:
    sql_query = f"DROP TABLE IF EXISTS {table};"

    conn = get_database_connection()
    cur = conn.cursor()

    try:
        cur.execute(sql_query)
    except Exception as e:
        logger.info(f"{e}", stack_info=True)
    finally:
        cur.close()
        conn.close()

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
    conn = get_database_connection()
    cur = conn.cursor()

    for table_name, columns in DATABASE_TABLE_SCHEMA.items():
        try:
            sql_query = (
                f"CREATE TABLE IF NOT EXISTS {table_name} ("
            )

            for column, data_type in columns.items():
                sql_query += f"{column} {data_type}, "

            sql_query = sql_query[:-2]
            sql_query += ");"

            cur.execute(sql_query)
            conn.commit()

            logger.info(f"Database table {table_name} created.")
        except Exception as e:
            logger.exception(f"Issue creating database table {table_name}.")

    cur.close()
    conn.close()


def delete_all_tables():
    conn = get_database_connection()
    cur = conn.cursor()
    try:
        for table_name in DATABASE_TABLE_SCHEMA.keys():
            cur.execute(f"DROP TABLE IF EXISTS {table_name};")
            conn.commit()
    except Exception as e:
        logger.error(f"Error deleting database tables: {e}", stack_info=True)
    finally:
        cur.close()
        conn.close()


def write_runner_status(runner_status: dict) -> None:
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
        "%s, %s, %s, %s, %s, %s, %s) "
        "ON CONFLICT(runner_name_pk) DO UPDATE SET "
        "active=excluded.active, "
        "adjusted_interval=excluded.adjusted_interval, "
        "default_interval=excluded.default_interval, "
        "current_update_success=excluded.current_update_success, "
        "previous_update_success=excluded.previous_update_success, "
        "epoch_time_previous_success=excluded.epoch_time_previous_success"
        ";"
    )
    values = (
        runner_status["runner_name_pk"],
        runner_status["active"],
        runner_status["adjusted_interval"],
        runner_status["default_interval"],
        runner_status["current_update_success"],
        runner_status["previous_update_success"],
        runner_status["epoch_time_previous_success"],
    )
    conn = get_database_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql_query, values)
        conn.commit()
        logger.info(
            f"Wrote runner status for {runner_status['runner_name_pk']}.\nStatus details:\n{runner_status}",
            extra={"runner": runner_status["runner_name_pk"]}
        )
    except Exception as e:
        logger.exception(stack_info=True)
    finally:
        cur.close()
        conn.close()


def update_open_option_positions(open_option_positions) -> None:
    set_table_field("open_option_positions", "still_alive", False)

    for position in open_option_positions:
        position_uuid_pk = position["id"]
        json_data = json.dumps(position)
        last_update_epoch_time = time.time()
        still_alive = True

        sql_query = (
            "INSERT INTO open_option_positions (position_uuid_pk, json_data, last_update_epoch_time, still_alive) "
            "VALUES (%s, %s, %s, %s) "
            "ON CONFLICT(position_uuid_pk) DO UPDATE SET "
            "json_data=excluded.json_data, "
            "last_update_epoch_time=excluded.last_update_epoch_time, "
            "still_alive=excluded.still_alive"
        )
        values = (position_uuid_pk, json_data, last_update_epoch_time, still_alive)
        
        conn = get_database_connection()
        cur = conn.cursor()
        try:
            cur.execute(sql_query, values)
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            logger.exception(f"Issue updating open option position: {e}", stack_info=True)
        finally:
             cur.close()
             conn.close()

    delete_rows_from_table_by_value("open_option_positions", "still_alive", False)


def update_open_option_positions_market_data(options_market_data: list) -> None:
    set_table_field("open_option_positions_market_data", "still_alive", False)

    for option in options_market_data:
        option_uuid_pk = option["instrument_id"]
        json_data = json.dumps(option)
        last_update_epoch_time = time.time()
        still_alive = True
        
        sql_query = (
            "INSERT INTO open_option_positions_market_data (option_uuid_pk, json_data, last_update_epoch_time, still_alive) "
            "VALUES (%s, %s, %s, %s) "
            "ON CONFLICT(option_uuid_pk) DO UPDATE SET "
            "json_data=excluded.json_data, "
            "last_update_epoch_time=excluded.last_update_epoch_time, "
            "still_alive=excluded.still_alive;"
        )
        values = (option_uuid_pk, json_data, last_update_epoch_time, still_alive)
        
        conn = get_database_connection()
        cur = conn.cursor()
        try:
            cur.execute(sql_query, values)
            conn.commit()
        except Exception as e:
            logger.exception(f"Issue updating open option position market data: {e}", stack_info=True)
        finally:
            cur.close()
            conn.close()
        
    delete_rows_from_table_by_value("open_option_positions_market_data", "still_alive", False)


def update_open_broker_option_orders(open_broker_orders: list) -> None:
    set_table_field("open_broker_option_orders", "still_alive", False)

    for order in open_broker_orders:
        order_uuid_pk = order["id"]
        json_data = json.dumps(order)
        last_update_epoch_time = time.time()
        still_alive = True
        
        sql_query = (
            "INSERT INTO open_broker_option_orders (order_uuid_pk, json_data, still_alive, last_update_epoch_time) "
            "VALUES (%s, %s, %s, %s) "
            "ON CONFLICT(order_uuid_pk) DO UPDATE SET "
            "json_data=excluded.json_data, "
            "still_alive=excluded.still_alive, "
            "last_update_epoch_time=excluded.last_update_epoch_time;"
        )
        values = (order_uuid_pk, json_data, still_alive, last_update_epoch_time)
        
        conn = get_database_connection()
        cur = conn.cursor()
        try:
            cur.execute(sql_query, values)
            conn.commit()
        except Exception as e:
            logger.exception(f"Issue updating open broker option order: {e}", stack_info=True)
        finally:
            cur.close()
            conn.close()

    delete_rows_from_table_by_value("open_broker_option_orders", "still_alive", False)


def update_open_broker_option_orders_market_data(option_market_data: list) -> None:
    set_table_field("open_broker_option_orders_market_data", "still_alive", False)

    for option in option_market_data:
        option_uuid_pk = option["instrument_id"]
        json_data = json.dumps(option)
        last_update_epoch_time = time.time()
        still_alive = True
        
        sql_query = (
            "INSERT INTO open_broker_option_orders_market_data (option_uuid_pk, json_data, last_update_epoch_time, still_alive) "
            "VALUES (%s, %s, %s, %s) "
            "ON CONFLICT(option_uuid_pk) DO UPDATE SET "
            "json_data=excluded.json_data, "
            "last_update_epoch_time=excluded.last_update_epoch_time, "
            "still_alive=excluded.still_alive;"
        )
        values = (option_uuid_pk, json_data, last_update_epoch_time, still_alive)
        
        conn = get_database_connection()
        cur = conn.cursor()
        try:
            cur.execute(sql_query, values)
            conn.commit()
        except Exception as e:
            logger.exception(f"Issue updating open_broker_option_orders_market_data: {e}", stack_info=True)
        finally:
            cur.close()
            conn.close()

    delete_rows_from_table_by_value("open_broker_option_orders_market_data", "still_alive", False)


def update_trigger_option_orders_market_data(option_market_data: list) -> None:
    set_table_field("trigger_option_orders_market_data", "still_alive", False)

    for option in option_market_data:
        option_uuid_pk = option["instrument_id"]
        json_data = json.dumps(option)
        last_update_epoch_time = time.time()
        still_alive = True
        
        sql_query = (
            "INSERT INTO trigger_option_orders_market_data (option_uuid_pk, json_data, last_update_epoch_time, still_alive) "
            "VALUES (%s, %s, %s, %s) "
            "ON CONFLICT(option_uuid_pk) DO UPDATE SET "
            "json_data=excluded.json_data, "
            "last_update_epoch_time=excluded.last_update_epoch_time, "
            "still_alive=excluded.still_alive;"
        )
        values = (option_uuid_pk, json_data, last_update_epoch_time, still_alive)
        
        conn = get_database_connection()
        cur = conn.cursor()
        try:
            cur.execute(sql_query, values)
            conn.commit()
        except Exception as e:
            logger.exception(f"Issue updating trigger_option_orders_market_data: {e}", stack_info=True)
        finally:
            cur.close()
            conn.close()

    delete_rows_from_table_by_value("trigger_option_orders_market_data", "still_alive", False)


def update_bracket_option_orders_market_data(option_market_data: list) -> None:
    set_table_field("bracket_option_orders_market_data", "still_alive", False)

    for option in option_market_data:
        option_uuid_pk = option["instrument_id"]
        json_data = json.dumps(option)
        last_update_epoch_time = time.time()
        still_alive = True
        
        sql_query = (
            "INSERT INTO bracket_option_orders_market_data (option_uuid_pk, json_data, last_update_epoch_time, still_alive) "
            "VALUES (%s, %s, %s, %s) "
            "ON CONFLICT(option_uuid_pk) DO UPDATE SET "
            "json_data=excluded.json_data, "
            "last_update_epoch_time=excluded.last_update_epoch_time, "
            "still_alive=excluded.still_alive;"
        )
        values = (option_uuid_pk, json_data, last_update_epoch_time, still_alive)
        
        conn = get_database_connection()
        cur = conn.cursor()
        try:
            cur.execute(sql_query, values)
            conn.commit()
        except Exception as e:
            logger.exception(f"Issue updating bracket_option_orders_market_data: {e}", stack_info=True)
        finally:
            cur.close()
            conn.close()

    delete_rows_from_table_by_value("bracket_option_orders_market_data", "still_alive", False)


def update_trailing_option_orders_market_data(option_market_data: list) -> None:
    set_table_field("trailing_option_orders_market_data", "still_alive", False)

    for option in option_market_data:
        option_uuid_pk = option["instrument_id"]
        json_data = json.dumps(option)
        last_update_epoch_time = time.time()
        still_alive = True
        
        sql_query = (
            "INSERT INTO trailing_option_orders_market_data (option_uuid_pk, json_data, last_update_epoch_time, still_alive) "
            "VALUES (%s, %s, %s, %s) "
            "ON CONFLICT(option_uuid_pk) DO UPDATE SET "
            "json_data=excluded.json_data, "
            "last_update_epoch_time=excluded.last_update_epoch_time, "
            "still_alive=excluded.still_alive;"
        )
        values = (option_uuid_pk, json_data, last_update_epoch_time, still_alive)
        
        conn = get_database_connection()
        cur = conn.cursor()
        try:
            cur.execute(sql_query, values)
            conn.commit()
        except Exception as e:
            logger.exception(f"Issue updating trailing_option_orders_market_data: {e}", stack_info=True)
        finally:
            cur.close()
            conn.close()

    delete_rows_from_table_by_value("trailing_option_orders_market_data", "still_alive", False)


def get_trailing_option_orders_list() -> list:
    conn = get_database_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    sql_query = "SELECT * FROM trailing_option_orders;"
    cur.execute(sql_query)
    results = cur.fetchall()

    trailing_orders_list = []
    for result in results:
        order_info = {}
        for key, value in result.items():
            order_info[key] = value

        trailing_orders_list.append(order_info)

    cur.close()
    conn.close()

    return trailing_orders_list

def get_trailing_option_order_market_data_by_order_uuid(option_uuid: str) -> dict | None:
    conn = get_database_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    sql_query = f"SELECT * FROM trailing_option_orders_market_data WHERE option_uuid_pk=%s;"
    values = (option_uuid, )
    cur.execute(sql_query, values)
    result = cur.fetchone()

    cur.close()
    conn.close()

    if result:
        order_market_data = {}
        for key, value in result.items():
            order_market_data[key] = value

        return order_market_data
    else:
        return None


def delete_rows_from_table_by_value(table, field, value) -> None:
    sql_query = f"DELETE FROM {table} WHERE {field}=%s;"
    values = (value, )

    conn = get_database_connection()
    cur = conn.cursor()

    try:
        cur.execute(sql_query, values)
        conn.commit()
    except Exception as e:
        logger.exception(f"{e}", stack_info=True)
    finally:
        cur.close()
        conn.close()


def set_table_field(table: str, field: str, value) -> None:
    sql_query = f"UPDATE {table} SET {field}=%s;"
    values = (value, )

    conn = get_database_connection()
    cur = conn.cursor()

    try:
        cur.execute(sql_query, values)
        conn.commit()
    except Exception as e:
        logger.exception(f"{e}", stack_info=True)
    finally:
        cur.close()
        conn.close()

def deactivate_orders(
        trigger_order_ids: list[int], 
        bracket_order_ids: list[int], 
        trailing_order_ids: list[int]
    ):
    conn = get_database_connection()
    cur = conn.cursor()

    for order_id in trigger_order_ids:
        sql_query = "UPDATE trigger_option_orders SET active=False WHERE order_id_pk=%s;"
        values = (order_id,)
        cur.execute(sql_query, values)
        conn.commit()

    for order_id in bracket_order_ids:
        sql_query = "UPDATE bracket_option_orders SET active=False WHERE order_id_pk=%s;"
        values = (order_id,)
        cur.execute(sql_query, values)
        conn.commit()

    for order_id in trailing_order_ids:
        sql_query = "UPDATE trailing_option_orders SET active=False WHERE order_id_pk=%s;"
        values = (order_id,)
        cur.execute(sql_query, values)
        conn.commit()

    cur.close()
    conn.close()

def mark_order_executed(table, order_id_pk):
    conn = get_database_connection()
    cur = conn.cursor()
    sql_query = f"UPDATE {table} SET executed=True WHERE order_id_pk=%s;"
    values = (order_id_pk,)
    cur.execute(sql_query, values)
    conn.commit()
    cur.close()
    conn.close()


def select_column_from_table(table: str, column: str) -> list:
    conn = get_database_connection()
    cur = conn.cursor()

    sql_query = f"SELECT {column} FROM {table};"
    cur.execute(sql_query)
    results = cur.fetchall()

    basic_list_result = []
    for item in results:
        basic_list_result.append(item[0])

    cur.close()
    conn.close()

    return basic_list_result

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
        active: bool,
        epoch_time_created_at: float,
        execute_only_after_trigger_order_ids: list[int],
        execute_only_after_bracket_order_ids: list[int],
        execute_only_after_trailing_order_ids: list[int],
        execution_deactivates_trigger_order_ids: list[int],
        execution_deactivates_bracket_order_ids: list[int],
        execution_deactivates_trailing_order_ids: list[int],
        buy_or_sell: str,
        credit_or_debit: str,
        symbol: str,
        strike: float,
        call_or_put: str,
        expiration_date: str,
        rh_option_uuid: str,
        quantity: int,
        message_on_success: str,
        message_on_failure: str,
        below_tick: float,
        above_tick: float,
        cutoff_price: float,
        max_order_attempts: int,
        emergency_order_fill_on_failure: bool,
        trigger_order_uuid: str,
    ) -> None:
	
    sql_query = (
        "INSERT INTO trigger_option_orders("
        "active, "
        "epoch_time_created_at, "
        "execute_only_after_trigger_order_ids, "
        "execute_only_after_trailing_order_ids, "
        "execute_only_after_bracket_order_ids, "
        "execution_deactivates_trigger_order_ids, "
        "execution_deactivates_trailing_order_ids, "
        "execution_deactivates_bracket_order_ids, "
        "buy_or_sell, "
        "credit_or_debit, "
        "symbol, "
        "strike, "
        "call_or_put, "
        "expiration_date, "
        "rh_option_uuid, "
        "quantity, "
        "message_on_success, "
        "message_on_failure, "
        "below_tick, "
        "above_tick, "
        "cutoff_price, "
        "max_order_attempts, "
        "emergency_order_fill_on_failure, "
        "trigger_order_uuid"
        ") "
        "VALUES ("
        "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s"
        ");"
    )
     
    values = (
        active, 
        epoch_time_created_at, 
        execute_only_after_trigger_order_ids, 
        execute_only_after_trailing_order_ids, 
        execute_only_after_bracket_order_ids, 
        execution_deactivates_trigger_order_ids, 
        execution_deactivates_trailing_order_ids, 
        execution_deactivates_bracket_order_ids, 
        buy_or_sell, 
        credit_or_debit, 
        symbol, 
        strike, 
        call_or_put, 
        expiration_date, 
        rh_option_uuid, 
        quantity, 
        message_on_success, 
        message_on_failure, 
        below_tick, 
        above_tick, 
        cutoff_price, 
        max_order_attempts, 
        emergency_order_fill_on_failure, 
        trigger_order_uuid
    )

    try:
        conn = get_database_connection()
        cur = conn.cursor()
        cur.execute(sql_query, values)
        conn.commit()
    except Exception as e:
        logger.exception(f"Issue inserting trigger order: {e}", stack_info=True)
    finally:
        cur.close()
        conn.close()
     

def insert_bracket_order(
        active: bool,
        epoch_time_created_at: float,
        execute_only_after_trigger_order_ids: list[int],
        execute_only_after_bracket_order_ids: list[int],
        execute_only_after_trailing_order_ids: list[int],
        execution_deactivates_trigger_order_ids: list[int],
        execution_deactivates_bracket_order_ids: list[int],
        execution_deactivates_trailing_order_ids: list[int],
        buy_or_sell: str,
        credit_or_debit: str,
        symbol: str,
        strike: float,
        call_or_put: str,
        expiration_date: str,
        rh_option_uuid: str,
        quantity: int,
        high_sell_mark_price: float,
        low_sell_mark_price: float,
        message_on_success: str,
        message_on_failure: str,
        below_tick: float,
        above_tick: float,
        cutoff_price: float,
        max_order_attempts: int,
        emergency_order_fill_on_failure: bool,
    ) -> None:
	
    sql_query = (
        "INSERT INTO bracket_option_orders("
        "active, "
        "epoch_time_created_at, "
        "execute_only_after_trigger_order_ids, "
        "execute_only_after_bracket_order_ids, "
        "execute_only_after_trailing_order_ids, "
        "execution_deactivates_trigger_order_ids, "
        "execution_deactivates_bracket_order_ids, "
        "execution_deactivates_trailing_order_ids, "
        "buy_or_sell, "
        "credit_or_debit, "
        "symbol, "
        "strike, "
        "call_or_put, "
        "expiration_date, "
        "rh_option_uuid, "
        "quantity, "
        "high_sell_mark_price, "
        "low_sell_mark_price, "
        "message_on_success, "
        "message_on_failure, "
        "below_tick, "
        "above_tick, "
        "cutoff_price, "
        "max_order_attempts, "
        "emergency_order_fill_on_failure"
        ") VALUES ("
        "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s"
        ");"
    )
     
    values = (
        active,
        epoch_time_created_at,
        execute_only_after_trigger_order_ids,
        execute_only_after_bracket_order_ids,
        execute_only_after_trailing_order_ids,
        execution_deactivates_trigger_order_ids,
        execution_deactivates_bracket_order_ids,
        execution_deactivates_trailing_order_ids,
        buy_or_sell,
        credit_or_debit,
        symbol,
        strike,
        call_or_put,
        expiration_date,
        rh_option_uuid,
        quantity,
        high_sell_mark_price,
        low_sell_mark_price,
        message_on_success,
        message_on_failure,
        below_tick,
        above_tick,
        cutoff_price,
        max_order_attempts,
        emergency_order_fill_on_failure,
    )

    try:
        conn = get_database_connection()
        cur = conn.cursor()
        cur.execute(sql_query, values)
        conn.commit()
    except Exception as e:
        logger.exception(f"Issue inserting bracket order: {e}", stack_info=True)
    finally:
        cur.close()
        conn.close()


def insert_trailing_order(
        active: bool,
        epoch_time_created_at: float,
        execute_only_after_trigger_order_ids: list[int],
        execute_only_after_bracket_order_ids: list[int],
        execute_only_after_trailing_order_ids: list[int],
        execution_deactivates_trigger_order_ids: list[int],
        execution_deactivates_bracket_order_ids: list[int],
        execution_deactivates_trailing_order_ids: list[int],
        buy_or_sell: str,
        credit_or_debit: str,
        symbol: str,
        strike: float,
        call_or_put: str,
        expiration_date: str,
        rh_option_uuid: str,
        quantity: int,
        message_on_success: str,
        message_on_failure: str,
        below_tick: float,
        above_tick: float,
        cutoff_price: float,
        max_order_attempts: int,
        emergency_order_fill_on_failure: bool,
        percent_from_high_sell_trigger: float,
        sell_at_specific_price: float,
        cost_basis: float
    ) -> None:
	
    sql_query = (
        "INSERT INTO trailing_option_orders("
        "active, "
        "epoch_time_created_at, "
        "execute_only_after_trigger_order_ids, "
        "execute_only_after_bracket_order_ids, "
        "execute_only_after_trailing_order_ids, "
        "execution_deactivates_trigger_order_ids, "
        "execution_deactivates_bracket_order_ids, "
        "execution_deactivates_trailing_order_ids, "
        "buy_or_sell, "
        "credit_or_debit, "
        "symbol, "
        "strike, "
        "call_or_put, "
        "expiration_date, "
        "rh_option_uuid, "
        "quantity, "
        "message_on_success, "
        "message_on_failure, "
        "below_tick, "
        "above_tick, "
        "cutoff_price, "
        "max_order_attempts, "
        "emergency_order_fill_on_failure, "
        "percent_from_high_sell_trigger, "
        "sell_at_specific_price, "
        "highest_price_since_order_placed"
        ") VALUES ("
        "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s"
        ");"
    )
     
    values = (
        active,
        epoch_time_created_at,
        execute_only_after_trigger_order_ids,
        execute_only_after_bracket_order_ids,
        execute_only_after_trailing_order_ids,
        execution_deactivates_trigger_order_ids,
        execution_deactivates_bracket_order_ids,
        execution_deactivates_trailing_order_ids,
        buy_or_sell,
        credit_or_debit,
        symbol,
        strike,
        call_or_put,
        expiration_date,
        rh_option_uuid,
        quantity,
        message_on_success,
        message_on_failure,
        below_tick,
        above_tick,
        cutoff_price,
        max_order_attempts,
        emergency_order_fill_on_failure,
        percent_from_high_sell_trigger, 
        sell_at_specific_price,
        cost_basis
    )

    conn = get_database_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql_query, values)
        conn.commit()
    except Exception as e:
        logger.exception(f"Issue inserting trailing order: {e}", stack_info=True)
    finally:
        cur.close()
        conn.close()

def get_executed_status_orders(trigger_order_ids, bracket_order_ids, trailing_order_ids):
    conn = get_database_connection()
    cur = conn.cursor()

    executed_status_list = []

    for order_id in trigger_order_ids:
        sql_query = "SELECT executed FROM trigger_option_orders WHERE order_id_pk=%s;"
        values = (order_id,)
        cur.execute(sql_query, values)
        result = cur.fetchone()[0]
        executed_status_list.append(result)

    for order_id in bracket_order_ids:
        sql_query = "SELECT executed FROM bracket_option_orders WHERE order_id_pk=%s;"
        values = (order_id,)
        cur.execute(sql_query, values)
        result = cur.fetchone()[0]
        executed_status_list.append(result)

    for order_id in trailing_order_ids:
        sql_query = "SELECT executed FROM trailing_option_orders WHERE order_id_pk=%s;"
        values = (order_id,)
        cur.execute(sql_query, values)
        result = cur.fetchone()[0]
        executed_status_list.append(result)

    cur.close()
    conn.close()

    return executed_status_list