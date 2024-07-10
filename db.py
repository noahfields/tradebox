import datetime
import os
import sqlite3

import pandas as pd

import config
import log

DB_FILEPATH = os.path.join(config.DATABASE_DIR, config.DATABASE_NAME)


def connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILEPATH)
    return conn


def create_orders_table() -> None:
    conn = connection()
    conn.execute('CREATE TABLE IF NOT EXISTS orders (order_id INTEGER PRIMARY KEY ASC, active INTEGER, created_at TEXT, executed INTEGER DEFAULT 0, execute_only_after_id INTEGER, execution_deactivates_order_id INTEGER, buy_sell TEXT, symbol TEXT, strike REAL, call_put TEXT, expiration_date TEXT, rh_option_uuid TEXT, market_limit TEXT, limit_price REAL, quantity INTEGER, message_on_success TEXT, message_on_failure TEXT, below_tick REAL, above_tick REAL, cutoff_price REAL, max_order_attempts INTEGER, emergency_order_fill_on_failure INTEGER);')
    conn.commit()
    conn.close()


def drop_orders_table() -> None:
    conn = connection()
    try:
        conn.execute('DROP TABLE orders;')
    except sqlite3.OperationalError as e:
        log.append(
            'db.drop_orders_table(): Could not drop orders table. Probably does not exist.')
    conn.commit()
    conn.close()


def insert_order(buy_sell: str, symbol: str,
                 expiration_date: str, strike: float, call_put: str,
                 quantity: int, market_limit: str,
                 emergency_order_fill_on_failure: bool,
                 active: bool, message_on_success: str, message_on_failure: str,
                 execute_only_after_id: int, execution_deactivates_order_id: int,
                 max_order_attempts: int, limit_price: float, rh_option_uuid: str,
                 below_tick: float, above_tick: float, cutoff_price: float) -> None:
    conn = connection()
    created_at = datetime.datetime.now()
    conn.execute(
        'INSERT INTO orders(created_at, rh_option_uuid, execute_only_after_id, '
        'buy_sell, symbol, expiration_date, strike, call_put, quantity, '
        'market_limit, below_tick, above_tick, cutoff_price, limit_price, '
        'message_on_success, message_on_failure, max_order_attempts, '
        'execution_deactivates_order_id, active, emergency_order_fill_on_failure) '
        'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);',
        (created_at, rh_option_uuid, execute_only_after_id, buy_sell, symbol,
         expiration_date, strike, call_put, quantity, market_limit,
         below_tick, above_tick, cutoff_price, limit_price, message_on_success,
         message_on_failure, max_order_attempts, execution_deactivates_order_id,
         active, emergency_order_fill_on_failure))
    conn.commit()
    conn.close()


def delete_order(order_id: int) -> None:
    conn = connection()
    conn.execute('DELETE FROM orders WHERE order_id = ?;', (order_id,))
    conn.commit()
    conn.close()


def delete_all_orders() -> None:
    conn = connection()
    conn.execute('DELETE FROM orders;')
    conn.commit()
    conn.close()


def fetch_order_sql(order_id: int) -> tuple:
    conn = connection()
    cur = conn.cursor()
    res = cur.execute('SELECT * FROM orders WHERE order_id=?;', (order_id,))
    orders = res.fetchall()
    order = orders[0]
    cur.close()
    conn.close()
    return order


def order_exists(order_id: int) -> bool:
    conn = connection()
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM orders WHERE order_id={order_id};')
    orders = cur.fetchall()
    if len(orders) >= 1:
        order_exists = True
    else:
        order_exists = False
    cur.close()
    conn.close()
    return order_exists


def get_order_series(order_id: int) -> pd.Series:
    conn = connection()
    order_dataframe = pd.read_sql(
        f'SELECT * FROM orders WHERE order_id={order_id};', conn)
    order_series = order_dataframe.loc[0]
    conn.close()
    return order_series


def fetch_all_orders_sql() -> list:
    conn = connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM orders;')
    orders = cur.fetchall()
    cur.close()
    conn.close()
    return orders


def fetch_all_orders_dataframe() -> pd.DataFrame:
    conn = connection()
    orders_dataframe = pd.read_sql('SELECT * FROM orders;', conn)
    conn.close()
    return orders_dataframe


def set_order_executed_status(order_id: int, executed: bool) -> None:
    conn = connection()
    cur = conn.cursor()
    cur.execute('UPDATE orders SET executed=? WHERE order_id=?',
                (executed, order_id,))
    conn.commit()
    cur.close()
    conn.close()


def set_order_active_status(order_id: int, active: bool) -> None:
    conn = connection()
    cur = conn.cursor()
    cur.execute('UPDATE orders SET active=? WHERE order_id=?',
                (active, order_id,))
    conn.commit()
    cur.close()
    conn.close()


def get_order_executed_status(order_id: int) -> bool:
    conn = connection()
    cur = conn.cursor()
    cur.execute('SELECT executed FROM orders WHERE order_id=?', (order_id,))
    res = cur.fetchall()[0][0]
    cur.close()
    conn.close()
    res = bool(int(res))
    return res


def get_console_formatted_orders_dataframe() -> pd.DataFrame:
    conn = connection()
    order_dataframe = pd.read_sql(
        'SELECT order_id, active, executed, execute_only_after_id, execution_deactivates_order_id,  buy_sell, symbol, strike, call_put, expiration_date, quantity, emergency_order_fill_on_failure FROM orders;', conn)
    conn.close()
    # minimize column name length for display
    order_dataframe.rename(columns={'order_id': 'id', 'execute_only_after_id': 'ex_after_id', 'execution_deactivates_order_id': 'ex_stops_id',
                                    'call_put': 'type', 'expiration_date': 'exp', 'quantity': 'qty', 'emergency_order_fill_on_failure': 'emergncy_fill'}, inplace=True)
    return order_dataframe


def set_execution_deactivates_order_id(order_id: int) -> None:
    """ pending deletion if not needed. probably can just use set_order_active_status """
    conn = connection()
    cur = conn.cursor()
    cur.execute(
        'SELECT execution_deactivates_order_id FROM orders WHERE order_id = ?', (order_id,))
    order_id_to_deactivate = str(cur.fetchall()[0][0])

    if order_id_to_deactivate == '':
        log.append(
            f'Order #{order_id} has no order to deactivate. Moving on.')
        return

    cur.execute('UPDATE orders SET active=? WHERE order_id=?',
                (0, order_id_to_deactivate))
    conn.commit()
    cur.close()
    conn.close()

    log.append(f'Deactivated order #{order_id_to_deactivate}.')
