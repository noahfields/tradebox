import sqlite3
import datetime
import traceback

import pandas as pd

import log


def connection():
    conn = sqlite3.connect('db.sqlite3')
    return conn


def create_orders_table():
    try:
        conn = connection()
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS orders (order_id INTEGER PRIMARY KEY ASC, active INTEGER, created_at TEXT, executed INTEGER DEFAULT 0, execute_only_after_id INTEGER, execution_deactivates_order_id INTEGER, buy_sell TEXT, symbol TEXT, strike REAL, call_put TEXT, expiration_date TEXT, rh_option_uuid TEXT, market_limit TEXT, limit_price REAL, quantity INTEGER, message_on_success TEXT, message_on_failure TEXT, below_tick REAL, above_tick REAL, cutoff_price REAL, max_order_attempts INTEGER);")
        conn.commit()
    except Exception as e:
        tb = traceback.format_exception(e)
        tb = ''.join(tb)
        print(tb)
        log.append(tb)
    finally:
        cur.close()
        conn.close()


def drop_orders_table():
    conn = connection()
    cur = conn.cursor()

    cur.execute("DROP TABLE orders;")

    conn.commit()
    cur.close()
    conn.close()


def create_order(rh_option_uuid, buy_sell, symbol, expiration_date, strike, call_put, quantity, market_limit, below_tick, above_tick, cutoff_price, limit_price, message_on_success, message_on_failure, execute_only_after_id, execution_deactivates_order_id, max_order_attempts, active):
    conn = connection()
    cur = conn.cursor()

    created_at = datetime.datetime.now()

    cur.execute("INSERT INTO orders(created_at, rh_option_uuid, execute_only_after_id, buy_sell, symbol, expiration_date, strike, call_put, quantity, market_limit, below_tick, above_tick, cutoff_price, limit_price, message_on_success, message_on_failure, max_order_attempts, execution_deactivates_order_id, active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                (created_at, rh_option_uuid, execute_only_after_id, buy_sell, symbol, expiration_date, strike, call_put, quantity, market_limit, below_tick, above_tick, cutoff_price, limit_price, message_on_success, message_on_failure, max_order_attempts, execution_deactivates_order_id, active))

    conn.commit()
    cur.close()
    conn.close()


def delete_order(order_id):
    conn = connection()
    cur = conn.cursor()

    cur.execute('DELETE FROM orders WHERE order_id = ?;', (order_id,))

    conn.commit()
    cur.close()
    conn.close()


def delete_all_orders():
    conn = connection()
    cur = conn.cursor()

    res = cur.execute('DELETE FROM orders;')

    conn.commit()
    cur.close()
    conn.close()


def fetch_order_sql(order_id):
    conn = connection()
    cur = conn.cursor()

    res = cur.execute('SELECT * FROM orders WHERE order_id=?;', (order_id,))

    orders = res.fetchall()
    order = orders[0]

    conn.commit()
    cur.close()
    conn.close()

    return order


def fetch_order_dataframe(order_id):
    conn = connection()
    order_dataframe = pd.read_sql(
        f'SELECT * FROM orders WHERE order_id={order_id};', conn)
    order_dataframe = order_dataframe.loc[0]
    conn.close()
    return order_dataframe


def fetch_all_orders_sql():
    conn = connection()
    cur = conn.cursor()

    cur.execute('SELECT * FROM orders;')
    orders = cur.fetchall()

    conn.commit()
    cur.close()
    conn.close()
    return orders


def fetch_all_orders_dataframe():
    conn = connection()
    order_dataframe = pd.read_sql('SELECT * FROM orders;', conn)
    conn.close()
    return order_dataframe


def mark_order_executed(order_id):
    conn = connection()
    cur = conn.cursor()

    cur.execute('UPDATE orders SET executed=1 WHERE order_id=?', (order_id,))

    conn.commit()
    cur.close()
    conn.close()


def set_order_active_status(order_id, active):
    conn = connection()
    cur = conn.cursor()

    cur.execute('UPDATE orders SET active=? WHERE order_id=?',
                (bool(active), order_id,))

    conn.commit()
    cur.close()
    conn.close()


def has_executed(order_id):
    conn = connection()
    cur = conn.cursor()

    cur.execute('SELECT executed FROM orders WHERE order_id=?', (order_id,))
    res = cur.fetchall()[0][0]

    cur.close()
    conn.close()

    res = bool(int(res))
    return res


def fetch_console_order_dataframe():
    conn = connection()
    order_dataframe = pd.read_sql(
        'SELECT order_id, active, executed, execute_only_after_id, buy_sell, symbol, strike, call_put, expiration_date, quantity FROM orders;', conn)
    conn.close()
    return order_dataframe
