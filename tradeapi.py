import datetime
import json
import os
import time

import pandas as pd
import robin_stocks.robinhood as r

import config
import db
import log
import notify


def login() -> None:
    res = r.login(config.ROBINHOOD_USERNAME,
                  config.ROBINHOOD_PASSWORD, expiresIn=config.ROBINHOOD_SESSION_EXPIRES_IN)
    log.append(f'Logged in to Robinhood. \n{res}')


def logout() -> None:
    try:
        r.logout()
    except Exception as e:
        log.append(f'Exception raised in tradeapi.logout(): {e}')

    try:
        home_dir = os.path.expanduser("~")
        data_dir = os.path.join(home_dir, ".tokens")
        creds_file = "robinhood.pickle"
        pickle_path = os.path.join(data_dir, creds_file)
        os.remove(pickle_path)
    except FileNotFoundError as e:
        log.append(f'Exception raised in tradeapi.logout(): {e}')

    log.append('Logged out of Robinhood.')


def create_order(buy_sell: str, symbol: str, expiration_date: str,
                 strike: float, call_put: str, quantity: int,
                 market_limit: str, emergency_order_fill_on_failure: bool,
                 active: bool, message_on_success: str,
                 message_on_failure: str, execute_only_after_id: int,
                 execution_deactivates_order_id: int,
                 max_order_attempts: int, limit_price: float = 0.0) -> None:

    instrument_data = r.options.get_option_instrument_data(
        symbol, expiration_date, strike, call_put)
    if instrument_data is None:
        msg = 'tradeapi.create_order(): r.options.get_option_instrument_data(' \
            + f'{symbol}, {expiration_date}, {strike}, {call_put}) ' \
            + 'returned None. Option likely does not exist. ' \
            + 'Check strike and expiration date.'
        log.append(msg)
        return

    rh_option_uuid = instrument_data['id']
    below_tick = instrument_data['min_ticks']['below_tick']
    above_tick = instrument_data['min_ticks']['above_tick']
    cutoff_price = instrument_data['min_ticks']['cutoff_price']

    db.insert_order(buy_sell, symbol, expiration_date, strike, call_put,
                    quantity, market_limit, emergency_order_fill_on_failure,
                    active, message_on_success, message_on_failure,
                    execute_only_after_id, execution_deactivates_order_id,
                    max_order_attempts, limit_price, rh_option_uuid,
                    below_tick, above_tick, cutoff_price)

    msg = f'Successfully created order for {buy_sell} {quantity} ' \
        + f'{symbol}, {expiration_date}, {strike}, {call_put}.'
    log.append(msg)


def execute_order(order_id: int) -> None:
    log.append(f'Begin tradeapi.py:execute_order() for order {order_id}.')

    # get order information from local database
    try:
        order_info = db.get_order_series(order_id)
    except KeyError:
        msg = f'Looks like order #{order_id} does not exist.' \
            + f'Aborting tradeapi.execute_order({order_id}).'
        log.append(msg)
        return

    # abort if inactive
    if bool(order_info['active']) is False:
        msg = f'tradeapi.execute_order(): order #{order_id} ' \
            + 'is not active. Aborting execution.'
        log.append(msg)
        return

    # abort if executed
    if bool(order_info['executed']) is True:
        msg = f'tradeapi.execute_order(): order #{order_id} ' \
            + 'has already executed. Aborting execution.'
        log.append(msg)
        return

    # abort if prerequisite order does not exist or is not executed
    if (db.order_exists(order_info['execute_only_after_id']) and
            not db.get_order_executed_status(order_info['execute_only_after_id'])):
        msg = 'rhapi.execute_order(): prerequisite ' \
            + f'{order_info["execute_only_after_id"]} ' \
            + 'not executed or does not exist.' \
            + f'Cancelling execution of order #{order_id}.'
        log.append(msg)
        return

    # mark trade as executed
    db.set_order_executed_status(order_id, True)
    log.append(f'Marked order number {order_id} as executed.')

    # set order as inactive
    db.set_order_active_status(order_id, False)
    log.append(f'Marked order number {order_id} as inactive.')

    # deactivate check
    db.set_order_active_status(
        order_info['execution_deactivates_order_id'], False)

    # select correct order function
    # CHANGE THIS TO throw an exception and catch it if order type is invalid
    # or fix conditionals
    if order_info['buy_sell'] == 'buy':
        if order_info['market_limit'] == 'market':
            execute_market_buy_order(order_info)
    elif order_info['buy_sell'] == 'sell':
        if order_info['market_limit'] == 'market':
            execute_market_sell_order(order_info)
    else:
        msg = 'No valid order type selected.' \
            + f'buy/sell: {order_info["buy_sell"]} ' \
            + f'market/limit: {order_info["market_limit"]}'
        log.append(msg)


def get_option_instrument_data(symbol: str, call_put: str, strike: float,
                               expiration_date: str) -> tuple[float, float, float, str]:
    data = r.options.get_option_instrument_data(
        symbol, expiration_date, strike, call_put)

    below_tick = data['min_ticks']['below_tick']
    above_tick = data['min_ticks']['above_tick']
    cutoff_price = data['min_ticks']['cutoff_price']
    option_uuid = data['id']

    return below_tick, above_tick, cutoff_price, option_uuid


def execute_market_buy_order(order_info: pd.Series) -> None:
    log.append(
        f'Begin execute_market_buy_order for order #{order_info["order_id"]}.')
    log.append(f'Tradebox order info: \n{order_info.to_string()}')

    number_of_trades_placed = 0
    opening_position_size = 0
    actual_closing_position_size = None
    current_position_size = 0
    goal_final_position_size = None

    open_option_positions = r.options.get_open_option_positions()
    for open_pos in open_option_positions:
        if open_pos['option_id'] == order_info['rh_option_uuid']:
            log.append(
                "Existing position info before any trades: \n" + json.dumps(open_pos))
            current_position_size = int(float(open_pos['quantity']))
            opening_position_size = current_position_size

    log.append(f'Opening position size: {opening_position_size}')
    log.append(f'Current position size: {current_position_size}')

    goal_final_position_size = current_position_size + \
        int(order_info['quantity'])
    log.append(f'Calculated goal final position size: {
               goal_final_position_size}')

    order_cancel_ids = []

    while (current_position_size < goal_final_position_size) and (number_of_trades_placed < int(order_info['max_order_attempts'])):
        remaining_quantity = goal_final_position_size - current_position_size
        log.append(f'Remaining quantity to buy: {remaining_quantity}')

        option_market_data = r.options.get_option_market_data_by_id(
            order_info['rh_option_uuid'])[0]
        log.append(f'Current raw market data: {
                   json.dumps(option_market_data)}')

        order_result = r.orders.order_buy_option_limit(
            'open', 'debit', option_market_data['ask_price'], order_info['symbol'], remaining_quantity,
            order_info['expiration_date'], order_info['strike'],
            optionType=order_info['call_put'], timeInForce='gtc')
        log.append(json.dumps(order_result))

        number_of_trades_placed += 1
        log.append(f'Number of trades placed: {number_of_trades_placed}')

        time.sleep(2)

        try:
            log.append(f'Cancelling order ID {order_result["id"]}.')
            order_cancel_ids.append(order_result['id'])
            r.orders.cancel_option_order(order_result['id'])
        except:
            pass

        time.sleep(4)

        open_option_positions = r.options.get_open_option_positions()
        for open_pos in open_option_positions:
            if open_pos['option_id'] == order_info['rh_option_uuid']:
                current_position_size = int(float(open_pos['quantity']))
        log.append(f'Updated open option positions: {current_position_size}')

    time.sleep(3)

    # closing trade info
    open_option_positions = r.options.get_open_option_positions()
    for open_pos in open_option_positions:
        if open_pos['option_id'] == order_info['rh_option_uuid']:
            current_position_size = int(float(open_pos['quantity']))
            actual_closing_position_size = current_position_size
    log.append(f'Opening position size: {opening_position_size}')
    log.append(f'Goal final position size: {goal_final_position_size}')
    log.append(f'Actual closing position size: {actual_closing_position_size}')
    log.append(f'Final number of trades placed: {number_of_trades_placed}')

    # dev: probably good until here

    if actual_closing_position_size is not None and isinstance(actual_closing_position_size, int):
        quantity_bought = actual_closing_position_size - opening_position_size
    else:
        quantity_bought = 0

    prepend_msg = f'Ex\'d #{order_info["order_id"]}. Bought {quantity_bought} {order_info["symbol"]} {
        order_info["call_put"]} {order_info["expiration_date"]} {order_info["strike"]}. Cur pos: {actual_closing_position_size}.'
    log.append(prepend_msg)

    if current_position_size < goal_final_position_size:
        log.append('tradeapi.execute_market_buy_order did not fill completely.')

        if bool(order_info['emergency_order_fill_on_failure']) is True:
            log.append('emergency buy fill is activated')
            quantity_to_buy = goal_final_position_size - current_position_size
            execute_buy_emergency_fill(
                order_info, quantity_to_buy, prepend_msg)
        else:
            log.append('No emergency fill ordered.')
            log.append(prepend_msg)
            notify.send_plaintext_email(prepend_msg)

    # re-cancel all orders at conclusion
    log.append(f'Cancelling {len(order_cancel_ids)} orders for safety.')
    for cancel_id in order_cancel_ids:
        try:
            log.append(f'Cancelling order ID {cancel_id}.')
            r.orders.cancel_option_order(order_result['id'])
        except:
            pass
        time.sleep(4)
    log.append('Cancelled all order IDs from execute_market_buy_order.')
    log.append('Completed execute_market_buy_order.')


def execute_market_sell_order(order_info: pd.Series) -> None:
    log.append(
        f'Begin execute_market_sell_order for order #{order_info["order_id"]}.')
    log.append("tradebox order info: \n" + order_info.to_string())

    number_of_trades_placed = 0
    opening_position_size = 0
    actual_closing_position_size = None
    current_position_size = 0
    goal_final_position_size = None

    open_option_positions = r.options.get_open_option_positions()
    for open_pos in open_option_positions:
        if open_pos['option_id'] == order_info['rh_option_uuid']:
            log.append(f'Existing position info before any trades: \n {
                       json.dumps(open_pos)}')
            current_position_size = int(float(open_pos['quantity']))
            opening_position_size = current_position_size

    log.append(f'Opening position size: {opening_position_size}')
    log.append(f'Current position size: {current_position_size}')

    goal_final_position_size = current_position_size - \
        int(order_info['quantity'])

    # in case the quantity to sell is greater than the total owned
    # this will close the position to zero
    # and stop the sell orders from failing
    if goal_final_position_size < 0:
        goal_final_position_size = 0
        log.append(
            f'Tradebox order is asking to sell more positions than are currently held in account. final_position_size revised to {goal_final_position_size} (should read 0).')
    log.append(f'Calculated final position size: {goal_final_position_size}')

    # collect order IDs to cancel at conclusion
    order_cancel_ids = []

    while (current_position_size > goal_final_position_size) and (number_of_trades_placed < order_info['max_order_attempts']):
        remaining_quantity = current_position_size - goal_final_position_size
        log.append(f'Remaining quantity to sell: {remaining_quantity}')

        option_market_data = r.options.get_option_market_data_by_id(
            order_info['rh_option_uuid'])[0]
        log.append(json.dumps(option_market_data))

        order_result = r.orders.order_sell_option_limit(
            'close', 'credit', option_market_data['bid_price'], order_info['symbol'], remaining_quantity,
            order_info['expiration_date'], order_info['strike'],
            optionType=order_info['call_put'], timeInForce='gtc')
        log.append(json.dumps(order_result))

        number_of_trades_placed += 1
        log.append(f'Number of trades placed: {number_of_trades_placed}')

        time.sleep(3)

        try:
            log.append(f'Cancelling order ID {order_result['id']}.')
            res = r.orders.cancel_option_order(order_result['id'])
            log.append(f'Result of cancellation: {json.dumps(res)}')
            order_cancel_ids.append(order_result['id'])
        except:
            pass

        time.sleep(3)

        # update position status
        position_still_exists = False
        open_option_positions = r.options.get_open_option_positions()
        log.append(
            f'Updated raw position info after trade #{number_of_trades_placed}: \n\n {open_option_positions}')
        for open_pos in open_option_positions:
            if open_pos['option_id'] == order_info['rh_option_uuid']:
                current_position_size = int(float(open_pos['quantity']))
                position_still_exists = True
        if (position_still_exists == False) or current_position_size == 0:
            current_position_size = 0
        log.append(
            f'Updated open option position quantity: {current_position_size}')

    time.sleep(1)

    # trade report items
    open_option_positions = r.options.get_open_option_positions()
    for open_pos in open_option_positions:
        if open_pos['option_id'] == order_info['rh_option_uuid']:
            actual_closing_position_size = int(float(open_pos['quantity']))
    log.append(f'Opening position size: {opening_position_size}')
    log.append(f'Goal final position size: {goal_final_position_size}')
    log.append(f'Actual closing position size: {actual_closing_position_size}')
    log.append(f'Final number of trades placed: {number_of_trades_placed}')

    # build initial message report
    quantity_sold = None
    if actual_closing_position_size is None:
        quantity_sold = opening_position_size
    else:
        quantity_sold = opening_position_size - actual_closing_position_size
    message = f'Ex\'d ord{order_info["order_id"]}. Sold {quantity_sold} {order_info["symbol"]} {order_info["call_put"]} {
        order_info["expiration_date"]} {order_info["strike"]}. Cur pos: {actual_closing_position_size}.'

    log.append(message)

    if bool(int(order_info['emergency_order_fill_on_failure'])) is True:
        if isinstance(actual_closing_position_size, int) and (actual_closing_position_size > goal_final_position_size):
            execute_sell_emergency_fill(order_info=order_info, quantity_to_sell=(
                actual_closing_position_size - goal_final_position_size), prepend_message=message)
    else:
        notify.send_plaintext_email(
            f'{message}. No emergency order submitted.')
        log.append('Email/text notification sent. No emergency fill.')

    # re-cancel all orders at conclusion
    log.append(f'Cancelling {len(order_cancel_ids)} orders for safety.')
    for cancel_id in order_cancel_ids:
        try:
            log.append(f'Cancelling order ID {cancel_id}.')
            r.orders.cancel_option_order(order_result['id'])
        except:
            pass
        time.sleep(4)
    log.append('Cancelled all order IDs from execute_market_sell_order.')


def cancel_all_robinhood_orders() -> None:
    r.orders.cancel_all_option_orders()


def get_console_open_robinhood_positions() -> pd.DataFrame:
    open_positions = r.options.get_open_option_positions()

    display_positions = []

    for open_position in open_positions:
        instrument_data = r.options.get_option_instrument_data_by_id(
            open_position['option_id'])
        quantity = int(float(open_position['quantity']))
        symbol = open_position['chain_symbol']
        average_price = round(float(open_position['average_price']), 2)
        strike = round(float(instrument_data['strike_price']), 2)
        call_put = instrument_data['type']
        expiration_date = instrument_data['expiration_date']

        market_data = r.options.get_option_market_data_by_id(
            open_position['option_id'])[0]

        adjusted_mark_price = round(
            float(market_data['adjusted_mark_price']), 2)

        display_position = {'symbol': symbol, 'call_put': call_put,
                            'expiration_date': expiration_date, 'strike': strike,
                            'quantity': quantity, 'average_price': average_price,
                            'current_mark': adjusted_mark_price}

        display_positions.append(display_position)

    positions_dataframe = pd.DataFrame(display_positions)
    return positions_dataframe


def execute_sell_emergency_fill(order_info: pd.Series, quantity_to_sell: int, prepend_message: str = '') -> None:
    log.append(f'emergency sell: trying to sell {quantity_to_sell} {order_info["symbol"]} {
               order_info["call_put"]} {order_info["strike"]} {order_info["expiration_date"]}')
    option_market_data = r.options.get_option_market_data_by_id(
        order_info['rh_option_uuid'])[0]

    bid_price = round(float(option_market_data['bid_price']), 2)
    log.append(f'emergency sell: bid price {bid_price}')

    # 50% discount
    sell_price = round(bid_price / 2, 2)
    log.append(f'emergency sell: 50% discount sell price {sell_price}')

    # find nearest tick (just using .05 cents here)
    sell_price = round(round(sell_price * 10) / 10, 2)
    if sell_price == 0:  # in case the option has bottomed out
        sell_price = 0.01

    log.append(f'emergency sell: revised sell price {sell_price}')

    order_result = r.orders.order_sell_option_limit(
        'close', 'credit', sell_price, order_info['symbol'], quantity_to_sell,
        order_info['expiration_date'], order_info['strike'],
        optionType=order_info['call_put'], timeInForce='gtc')

    log.append(f'emergency sell: sell order result: {
               json.dumps(order_result)}')

    time.sleep(20)

    res = r.orders.cancel_option_order(order_result['id'])
    log.append(f'Emergency order made. Cancelling after 20 seconds. Result of cancellation: {
               json.dumps(res)}')

    time.sleep(5)

    open_option_positions = r.options.get_open_option_positions()
    after_emergency_position_quantity = 0
    for open_pos in open_option_positions:
        if open_pos['option_id'] == order_info['rh_option_uuid']:
            after_emergency_position_quantity = int(
                float(open_pos['quantity']))

    log.append(f'emergency sell: quantity after emergency sell {
               after_emergency_position_quantity}')

    message = f'ES new qty: {after_emergency_position_quantity} {
        datetime.datetime.now().strftime("%d %H:%M:%S")}'

    log.append(f'{prepend_message} {message}')
    notify.send_plaintext_email(f'{prepend_message} {message}')
    log.append('Email/text notification sent. Emergency fill executed.')


def execute_buy_emergency_fill(order_info: pd.Series, quantity_to_buy: int, prepend_message: str = '') -> None:
    log.append(f'emergency buy: trying to buy {quantity_to_buy} {order_info["symbol"]} {
               order_info["call_put"]} {order_info["strike"]} {order_info["expiration_date"]}')

    option_market_data = r.options.get_option_market_data_by_id(
        order_info['rh_option_uuid'])[0]

    ask_price = round(float(option_market_data['ask_price']), 2)
    log.append(f'emergency buy: bid price {ask_price}')

    # 50% higher limit price than ask price
    buy_price = round((ask_price * 1.5) + 0.05, 2)
    log.append(f'emergency buy: 50% higher buy price plus 5 cents {buy_price}')

    # find nearest tick (just using .05 cents here)
    buy_price = round(round(buy_price * 10) / 10, 2)

    log.append(f'emergency buy: revised buy price {buy_price}')

    order_result = r.orders.order_buy_option_limit(
        'close', 'credit', buy_price, order_info['symbol'], quantity_to_buy,
        order_info['expiration_date'], order_info['strike'],
        optionType=order_info['call_put'], timeInForce='gtc')

    log.append(f'emergency buy: buy order result: {
               json.dumps(order_result)}')

    time.sleep(10)

    res = None
    try:
        res = r.orders.cancel_option_order(order_result['id'])
    except:
        res = 'none'
    finally:
        log.append(f'Emergency buy order made. Cancelling after 10 seconds. Result of cancellation: {
            json.dumps(res)}')

    time.sleep(5)

    open_option_positions = r.options.get_open_option_positions()
    after_emergency_position_quantity = None
    for open_pos in open_option_positions:
        if open_pos['option_id'] == order_info['rh_option_uuid']:
            after_emergency_position_quantity = int(
                float(open_pos['quantity']))

    log.append(f'emergency buy: quantity after emergency buy {
               after_emergency_position_quantity}')

    message = f'EB new qty: {after_emergency_position_quantity} {
        datetime.datetime.now().strftime("%d %H:%M:%S")}'

    log.append(f'{prepend_message} {message}')
    notify.send_plaintext_email(f'{prepend_message} {message}')
    log.append('Email/text notification sent. Emergency buy fill executed.')
