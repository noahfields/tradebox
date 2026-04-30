from contextlib import contextmanager
import logging
import os
import json
import psycopg2
import psycopg2.extras
import psycopg2.extensions
import time
from typing import Any

import config
import schema


# Define the casting function
def cast_decimal(value, cur):
    if value is None:
        return None
    return float(value)

# Create a new type caster for DECIMAL (OID 1700)
DEC2FLOAT = psycopg2.extensions.new_type(
    psycopg2.extensions.DECIMAL.values, 
    'DEC2FLOAT', 
    cast_decimal
)

# Register it globally
psycopg2.extensions.register_type(DEC2FLOAT)

logger = logging.getLogger(__name__)


def create_all_tables():
    conn = get_database_connection()
    cur = conn.cursor()

    for table_name, columns in schema.DATABASE_TABLES.items():
        sql_query = (f"CREATE TABLE IF NOT EXISTS {table_name} (")

        for column, data_type in columns.items():
            sql_query += f"{column} {data_type}, "

        sql_query = sql_query[:-2]
        sql_query += ");"

        cur.execute(sql_query)
        conn.commit()

        logger.info(f"Database table {table_name} created.")

    cur.close()
    conn.close()


def drop_all_tables():
    for table in schema.DATABASE_TABLES.keys():
        drop_table(table)


def drop_table(table: str) -> None:
    sql_query = f"DROP TABLE IF EXISTS {table};"

    conn = get_database_connection()
    cur = conn.cursor()

    try:
        cur.execute(sql_query)
        conn.commit()
    except Exception as e:
        logger.info(f"{e}", stack_info=True)
    finally:
        cur.close()
        conn.close()


def get_database_connection() -> psycopg2.extensions.connection:
	try:
		conn = psycopg2.connect(config.DATABASE_URI)
		conn.autocommit = False
		return conn
	except Exception as e:
		logger.exception(f"{e}", stack_info=True)


def get_all_runners_status(return_json=False):
    conn = get_database_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    sql_query = "SELECT * FROM runners;"
    cur.execute(sql_query)
    results = cur.fetchall()

    cur.close()
    conn.close()

    runners_status_list = []
    for result in results:
        runner_info = {}
        for key, value in result.items():
            runner_info[key] = value

        runners_status_list.append(runner_info)

    if return_json:
        return json.dumps(runners_status_list)
    else:
        return runners_status_list


def get_runner_status(runner_name_pk: str) -> dict | None:
    conn = get_database_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    sql_query = (f"SELECT * FROM runners WHERE runner_name_pk='{runner_name_pk}';")

    cur.execute(sql_query)
    result = cur.fetchone()

    cur.close()
    conn.close()

    if result:
        runner_status = {}
        for key, value in result.items():
            runner_status[key] = value

        logger.info(f"Got runner status for {runner_name_pk}:\n{runner_status}", extra={"runner": runner_name_pk})
        return runner_status
    else:
        logger.error(f"No runner status entry for {runner_name_pk}. Returning None.", extra={"runner": runner_name_pk})
        return None


def write_runner_status(runner_status: dict) -> None:
    sql_query = (
        "INSERT INTO runners ("
        "runner_name_pk, "
        "active, "
        "adjusted_interval, "
        "default_interval, "
        "current_update_success, "
        "previous_update_success, "
        "epoch_time_previous_success"
        ") VALUES ("
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
        str(runner_status["runner_name_pk"]),
        bool(runner_status["active"]),
        int(runner_status["adjusted_interval"]),
        int(runner_status["default_interval"]),
        bool(runner_status["current_update_success"]),
        bool(runner_status["previous_update_success"]),
        float(runner_status["epoch_time_previous_success"]),
    )
    conn = get_database_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql_query, values)
        conn.commit()
        logger.info(
            f"Wrote runner status for {runner_status['runner_name_pk']}.\n"
            f"Status details:\n{runner_status}",
            extra={"runner": runner_status["runner_name_pk"]}
        )
    except Exception as e:
        logger.exception(f"{e}", stack_info=True, extra={"runner": runner_status["runner_name_pk"]})
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


def update_open_option_positions_instrument_data(options_instrument_data: list) -> None:
    set_table_field("open_option_positions_instrument_data", "still_alive", False)

    for option in options_instrument_data:
        option_uuid_pk = option["id"]
        json_data = json.dumps(option)
        last_update_epoch_time = time.time()
        still_alive = True
        
        sql_query = (
            "INSERT INTO open_option_positions_instrument_data (option_uuid_pk, json_data, last_update_epoch_time, still_alive) "
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
            logger.exception(f"Issue updating open option position instrument data: {e}", stack_info=True)
        finally:
            cur.close()
            conn.close()
        
    delete_rows_from_table_by_value("open_option_positions_instrument_data", "still_alive", False)


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


def update_portfolio_profile(portfolio_profile_data: dict) -> None:
    single_id = 1
    json_data = json.dumps(portfolio_profile_data)
    last_update_epoch_time = time.time()
        
    sql_query = (
            "INSERT INTO portfolio_profile (single_id, json_data, last_update_epoch_time) "
            "VALUES (%s, %s, %s) "
            "ON CONFLICT(single_id) DO UPDATE SET "
            "json_data=excluded.json_data, "
            "last_update_epoch_time=excluded.last_update_epoch_time;"
        )

    values = (single_id, json_data, last_update_epoch_time)
        
    conn = get_database_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql_query, values)
        conn.commit()
    except Exception as e:
        logger.exception(f"Issue updating portfolio_profile: {e}", stack_info=True)
    finally:
        cur.close()
        conn.close()


def get_json_portfolio_profile():
    sql_query = "SELECT * FROM portfolio_profile WHERE single_id=1;"

    conn = get_database_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql_query)
        portfolio_profile = cur.fetchall()
        print("AAAAAAAAAA\nAAAAAAAAA")
        print(portfolio_profile)

        # try:
        #     res = {
        #         "portfolio_profile": json.dumps(portfolio_profile[0][1]), 
        #         "last_update_epoch_time": json.dumps(float(portfolio_profile[0][2])),
        #     }
        # except:
        #     res = {
        #         "portfolio_profile": None, 
        #         "last_update_epoch_time": None,
        #     }

        cur.close()
        conn.close()
        print(json.dumps(portfolio_profile))
        return json.dumps(portfolio_profile)
    except Exception as e:
        logger.exception(f"Issue getting info from table portfolio_profile: {e}", stack_info=True)
        cur.close()
        conn.close()
        return('nothing')


def get_open_option_positions(return_json=False):
    sql_query = "SELECT * FROM open_option_positions;"

    conn = get_database_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql_query)
        open_option_positions = cur.fetchall()

        # try:
        #     res = {
        #         "portfolio_profile": json.dumps(portfolio_profile[0][1]), 
        #         "last_update_epoch_time": json.dumps(float(portfolio_profile[0][2])),
        #     }
        # except:
        #     res = {
        #         "portfolio_profile": None, 
        #         "last_update_epoch_time": None,
        #     }

        cur.close()
        conn.close()
        if return_json == True:
            print(json.dumps(open_option_positions))
            return json.dumps(open_option_positions)
        else:
            print(open_option_positions)
            return open_option_positions
    except Exception as e:
        logger.exception(f"Issue getting open_option_positions: {e}", stack_info=True)
        cur.close()
        conn.close()
        return('nothing')


def update_open_broker_option_orders_instrument_data(options_instrument_data: list) -> None:
    set_table_field("open_broker_option_orders_instrument_data", "still_alive", False)

    for option in options_instrument_data:
        option_uuid_pk = option["id"]
        json_data = json.dumps(option)
        last_update_epoch_time = time.time()
        still_alive = True
        
        sql_query = (
            "INSERT INTO open_broker_option_orders_instrument_data (option_uuid_pk, json_data, last_update_epoch_time, still_alive) "
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
            logger.exception(f"Issue updating open broker option orders instrument data: {e}", stack_info=True)
        finally:
            cur.close()
            conn.close()
        
    delete_rows_from_table_by_value("open_broker_option_orders_instrument_data", "still_alive", False)


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


def update_trailing_sell_option_orders_market_data(option_market_data: list) -> None:
    set_table_field("trailing_sell_option_orders_market_data", "still_alive", False)

    for option in option_market_data:
        option_uuid_pk = option["instrument_id"]
        json_data = json.dumps(option)
        last_update_epoch_time = time.time()
        still_alive = True
        
        sql_query = (
            "INSERT INTO trailing_sell_option_orders_market_data (option_uuid_pk, json_data, last_update_epoch_time, still_alive) "
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
            logger.exception(f"Issue updating trailing_sell_option_orders_market_data: {e}", stack_info=True)
        finally:
            cur.close()
            conn.close()

    delete_rows_from_table_by_value("trailing_sell_option_orders_market_data", "still_alive", False)


def get_all_from_table(table: str) -> list[dict]:
    conn = get_database_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    sql_query = f"SELECT * FROM {table};"
    cur.execute(sql_query)
    results = cur.fetchall()

    result_list = []
    for result in results:
        item_info = {}
        for key, value in result.items():
            item_info[key] = value

        result_list.append(item_info)

    cur.close()
    conn.close()

    return result_list


def get_single_row_from_table(table: str, where_field: str, where_value: Any) -> dict | None:
    conn = get_database_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    sql_query = f"SELECT * FROM {table} WHERE {where_field}=%s;"
    values = (where_value, )

    result = None
    try:
        cur.execute(sql_query, values)
        result = cur.fetchone()
    except Exception as e:
        logger.exception(f"Issue fetching single row from {table} where {where_field}={where_value}: {e}", stack_info=True)
        result = None
    finally:
        cur.close()
        conn.close()

    if result:
        row_data = {}
        for key, value in result.items():
            row_data[key] = value

        return row_data
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


def set_table_field(table: str, field: str, value: Any) -> None:
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
    ) -> None:
    conn = get_database_connection()
    cur = conn.cursor()

    for order_id in trigger_order_ids:
        sql_query = "UPDATE trigger_option_orders SET active=False WHERE order_id_pk=%s;"
        values = (order_id,)
        cur.execute(sql_query, values)
        conn.commit()

    for order_id in bracket_order_ids:
        sql_query = "UPDATE bracket_sell_option_orders SET active=False WHERE order_id_pk=%s;"
        values = (order_id,)
        cur.execute(sql_query, values)
        conn.commit()

    for order_id in trailing_order_ids:
        sql_query = "UPDATE trailing_sell_option_orders SET active=False WHERE order_id_pk=%s;"
        values = (order_id,)
        cur.execute(sql_query, values)
        conn.commit()

    cur.close()
    conn.close()


def set_table_field_value_where(
        table: str, 
        field: str, 
        field_value: Any, 
        where_field: str, 
        where_value: Any
    ) -> None:
    sql_query = f"UPDATE {table} SET {field}=%s WHERE {where_field}=%s;"
    values = (field_value, where_value)

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


def update_trailing_sell_option_order_highest_price_since_order_placed(
        order_id_pk: int, 
        highest_price_since_order_placed: float
    ) -> None:
    conn = get_database_connection()
    cur = conn.cursor()

    sql_query = "UPDATE trailing_sell_option_orders SET highest_price_since_order_placed=%s WHERE order_id_pk=%s;"
    values = (highest_price_since_order_placed, order_id_pk)
    try:
        cur.execute(sql_query, values)
        conn.commit()
    except Exception as e:
        logger.exception(f"Issue updating highest_price_since_order_placed: {e}", stack_info=True)
    finally:
        cur.close()
        conn.close()

    
def set_table_field_where(table: str, field: str, field_value: Any, where_field: str, where_value: Any) -> None:
    sql_query = f"UPDATE {table} SET {field}=%s WHERE {where_field}=%s;"
    values = (field_value, where_value)

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
        max_mark_order_attempts: int,
        max_spread_order_attempts: int,
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
        "max_mark_order_attempts, "
        "max_spread_order_attempts, "
        "emergency_order_fill_on_failure, "
        "trigger_order_uuid"
        ") "
        "VALUES ("
        "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s"
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
        max_mark_order_attempts, 
        max_spread_order_attempts,
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
        robinhood_option_uuid: str,
        quantity: int,
        high_sell_mark_price: float,
        low_sell_mark_price: float,
        message_on_success: str,
        message_on_failure: str,
        below_tick: float,
        above_tick: float,
        cutoff_price: float,
        max_mark_order_attempts: int,
        max_spread_order_attempts: int,
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
        "robinhood_option_uuid, "
        "quantity, "
        "high_sell_mark_price, "
        "low_sell_mark_price, "
        "message_on_success, "
        "message_on_failure, "
        "below_tick, "
        "above_tick, "
        "cutoff_price, "
        "max_mark_order_attempts, "
        "max_spread_order_attempts, "
        "emergency_order_fill_on_failure"
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
        robinhood_option_uuid,
        quantity,
        high_sell_mark_price,
        low_sell_mark_price,
        message_on_success,
        message_on_failure,
        below_tick,
        above_tick,
        cutoff_price,
        max_mark_order_attempts,
        max_spread_order_attempts,
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


def insert_trailing_sell_order(
        active: bool,
        epoch_time_created_at: float,
        executed: bool,
        execute_only_after_trigger_order_ids: list[int],
        execute_only_after_bracket_sell_order_ids: list[int],
        execute_only_after_trailing_sell_order_ids: list[int],
        execution_deactivates_trigger_order_ids: list[int],
        execution_deactivates_bracket_sell_order_ids: list[int],
        execution_deactivates_trailing_sell_order_ids: list[int],
        quantity: int,
        symbol: str,
        call_or_put: str,
        expiration_date: str,
        strike: float,
        below_tick: float,
        above_tick: float,
        cutoff_price: float,
        robinhood_option_uuid: str,
        message_on_success: str,
        message_on_failure: str,
        max_mark_order_attempts: int,
        max_spread_order_attempts: int,
        emergency_order_fill_on_failure: bool,   
        percent_from_high_sell_trigger: float,
        sell_at_specific_price: float,
        purchase_price: float
    ) -> None:
	
    sql_query = (
        "INSERT INTO trailing_sell_option_orders("
        "active, "
        "epoch_time_created_at, "
        "executed, "
        "execute_only_after_trigger_order_ids, "
        "execute_only_after_bracket_sell_order_ids, "
        "execute_only_after_trailing_sell_order_ids, "
        "execution_deactivates_trigger_order_ids, "
        "execution_deactivates_bracket_sell_order_ids, "
        "execution_deactivates_trailing_sell_order_ids, "
        "quantity, "
        "symbol, "
        "call_or_put, "
        "expiration_date, "
        "strike, "
        "below_tick, "
        "above_tick, "
        "cutoff_price, "
        "robinhood_option_uuid, "
        "message_on_success, "
        "message_on_failure, "
        "max_mark_order_attempts, "
        "max_spread_order_attempts, "
        "emergency_order_fill_on_failure, "
        "percent_from_high_sell_trigger, "
        "sell_at_specific_price, "
        "purchase_price"
        ") VALUES ("
        "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s"
        ");"
    )
     
    values = (
        active, 
        epoch_time_created_at, 
        executed, 
        execute_only_after_trigger_order_ids, 
        execute_only_after_bracket_sell_order_ids, 
        execute_only_after_trailing_sell_order_ids, 
        execution_deactivates_trigger_order_ids, 
        execution_deactivates_bracket_sell_order_ids, 
        execution_deactivates_trailing_sell_order_ids, 
        quantity, 
        symbol, 
        call_or_put, 
        expiration_date, 
        strike, 
        below_tick, 
        above_tick, 
        cutoff_price, 
        robinhood_option_uuid, 
        message_on_success, 
        message_on_failure, 
        max_mark_order_attempts, 
        max_spread_order_attempts,
        emergency_order_fill_on_failure, 
        percent_from_high_sell_trigger, 
        sell_at_specific_price, 
        purchase_price
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
        sql_query = "SELECT executed FROM bracket_sell_option_orders WHERE order_id_pk=%s;"
        values = (order_id,)
        cur.execute(sql_query, values)
        result = cur.fetchone()[0]
        executed_status_list.append(result)

    for order_id in trailing_order_ids:
        sql_query = "SELECT executed FROM trailing_sell_option_orders WHERE order_id_pk=%s;"
        values = (order_id,)
        cur.execute(sql_query, values)
        result = cur.fetchone()[0]
        executed_status_list.append(result)

    cur.close()
    conn.close()

    return executed_status_list


def get_rounded_epoch_time(significant_figures=2):
    return round(time.time(), significant_figures)


def clear_all_tables():
    conn = get_database_connection()
    cur = conn.cursor()

    for table in schema.DATABASE_TABLES.keys():
        print(table)
        sql_query = f"DELETE FROM {table};"
        cur.execute(sql_query)
        conn.commit()

    cur.close()
    conn.close()


