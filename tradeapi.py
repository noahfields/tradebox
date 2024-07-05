import json
import os
import traceback
import time

import pandas as pd
import robin_stocks.robinhood as r

import db
import log
import config


# ready for live testing


def login():
    try:
        res = r.login(config.robinhood_username,
                      config.robinhood_password, expiresIn='172800')
        log.append(json.dumps(res))
    except Exception as e:
        tb = traceback.format_exception(e)
        tb = ''.join(tb)
        log.append('Problem at tradeapi.login()')
        log.append(tb)


def logout():
    try:
        r.logout()
        os.remove('~/.tokens/robinhood.pickle')
    except Exception as e:
        tb = traceback.format_exception(e)
        tb = ''.join(tb)
        print('Problem at tradeapi.logout()')
        print(tb)
        log.append('Problem at tradeapi.logout()')
        log.append(tb)


# ready for live testing


def create_order(buy_sell, symbol, expiration_date, strike, call_put, quantity,
                 market_limit, limit_price=0, active=True, message_on_success='',
                 message_on_failure='', execute_only_after_id='',
                 execution_deactivates_order_id='', max_order_attempts=10):
    print(f'buysell {buy_sell}')
    print(f'symbol {symbol}')
    print(f'expiration_date {expiration_date}')
    print(type(expiration_date))
    print(f'strike {strike}')
    print(f'callput {call_put}')
    instrument_data = r.options.get_option_instrument_data(
        symbol, expiration_date, strike, call_put)
    if instrument_data == None:
        log.append(
            f'tradeapi.create_order(): r.options.get_option_instrument_data({symbol}, {expiration_date}, {strike}, {call_put}) returned None')
        return

    below_tick = instrument_data['min_ticks']['below_tick']
    above_tick = instrument_data['min_ticks']['above_tick']
    cutoff_price = instrument_data['min_ticks']['cutoff_price']
    rh_option_uuid = instrument_data['id']

    db.create_order(rh_option_uuid, buy_sell, symbol, expiration_date, strike, call_put, quantity, market_limit, below_tick,
                    above_tick, cutoff_price, limit_price, message_on_success, message_on_failure, execute_only_after_id, execution_deactivates_order_id, max_order_attempts, active)

    msg = f'Successfully created order for {buy_sell} {quantity} {symbol}, {expiration_date}, {strike}, {call_put}.'
    log.append(msg)

# ready for live testing


def execute_order(order_id):
    log.append(f'Begin execute_order for order {order_id}.')

    login()
    order_info = db.fetch_order_dataframe(order_id)

    # is order active?
    if bool(order_info['active']) == False:
        log.append(
            f'tradeapi.execute_order(): order #{order_id} is not active. Aborting execution.')
        return

    # has order already executed?
    if bool(order_info['executed']) == True:
        log.append(
            f'tradeapi.execute_order(): order #{order_id} has already executed. Aborting execution.')
        return

    # has a prerequisite order executed?
    if order_info['execute_only_after_id'] != '':
        if not db.has_executed(order_info['execute_only_after_id']):
            log.append(
                f'rhapi.execute_order(): prerequisite {order_info["execute_only_after_id"]} not executed. Cancelling execution of order #{order_id}')
            return

    # select correct order function
    if order_info['buy_sell'] == 'buy':
        if order_info['market_limit'] == 'market':
            execute_market_buy_order(order_info)
        if order_info['market_limit'] == 'limit':
            execute_limit_buy_order(order_info)

    if order_info['buy_sell'] == 'sell':
        if order_info['market_limit'] == 'market':
            execute_market_sell_order(order_info)
        if order_info['market_limit'] == 'limit':
            execute_limit_sell_order(order_info)

    # mark trade as executed
    db.mark_order_executed(order_id)
    log.append(f'Marked order number {order_id} as executed.')

    # set order as inactive
    db.set_order_active_status(order_id, False)
    log.append(f'Marked order number {order_id} as inactive.')

# ready for live testing


def get_option_instrument_data(symbol, call_put, strike, expiration_date):
    login()

    data = r.options.get_option_instrument_data(
        symbol, expiration_date, strike, call_put)

    below_tick = data['min_ticks']['below_tick']
    above_tick = data['min_ticks']['above_tick']
    cutoff_price = data['min_ticks']['cutoff_price']
    option_uuid = data['id']

    return below_tick, above_tick, cutoff_price, option_uuid

# ready for live testing


def execute_market_buy_order(order_info):
    log.append(
        f'Begin execute_market_buy_order for order #{order_info["order_id"]}.')
    log.append("tradebox order info: \n" + order_info.to_string())

    # metrics to report at conclusion
    number_of_trades_placed = 0
    opening_position_size = 'none'
    actual_closing_position_size = 'none'

    current_position_size = 0
    open_option_positions = r.options.get_open_option_positions()
    for open_pos in open_option_positions:
        if open_pos['option_id'] == order_info['rh_option_uuid']:
            log.append(
                "Existing position info before any trades: \n" + json.dumps(open_pos))
            current_position_size = int(float(open_pos['quantity']))
            opening_position_size = current_position_size

    log.append(f'Opening position size: {opening_position_size}')
    log.append(f'Current position size: {current_position_size}')

    final_position_size = current_position_size + int(order_info['quantity'])

    log.append(f'Calculated final position size: {final_position_size}')

    order_cancel_ids = []

    while (current_position_size < final_position_size) and (number_of_trades_placed < order_info['max_order_attempts']):
        remaining_quantity = final_position_size - current_position_size
        log.append(f'Remaining quantity to buy: {remaining_quantity}')

        option_market_data = r.options.get_option_market_data_by_id(
            order_info['rh_option_uuid'])[0]
        log.append(json.dumps(option_market_data))

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
            r.orders.cancel_option_order(order_result['id'])
            order_cancel_ids.append(order_result['id'])
        except:
            pass

        time.sleep(4)

        open_option_positions = r.options.get_open_option_positions()
        for open_pos in open_option_positions:
            if open_pos['option_id'] == order_info['rh_option_uuid']:
                current_position_size = int(float(open_pos['quantity']))
        log.append(f'Updated open option positions: {current_position_size}')

    time.sleep(1)

    # make sure all orders are actually cancelled at conclusion
    log.append(f'Cancelling {len(order_cancel_ids)} orders for safety.')
    for cancel_id in order_cancel_ids:
        try:
            log.append(f'Cancelling order ID {cancel_id}.')
            r.orders.cancel_option_order(order_result['id'])
        except:
            pass
        time.sleep(5)
    log.append('Cancelled all order IDs.')

    # log trade metrics
    open_option_positions = r.options.get_open_option_positions()
    for open_pos in open_option_positions:
        if open_pos['option_id'] == order_info['rh_option_uuid']:
            actual_closing_position_size = int(float(open_pos['quantity']))
    log.append(f'Opening position size: {opening_position_size}')
    log.append(f'Goal final position size: {final_position_size}')
    log.append(f'Actual closing position size: {actual_closing_position_size}')
    log.append(f'Final number of trades placed: {number_of_trades_placed}')

# ready for live testing


def execute_market_sell_order(order_info):
    log.append(
        f'Begin execute_market_sell_order for order #{order_info["order_id"]}.')
    log.append("tradebox order info: \n" + order_info.to_string())

    # metrics to report at conclusion
    number_of_trades_placed = 0
    opening_position_size = 'none'
    actual_closing_position_size = 'none'

    current_position_size = 0
    open_option_positions = r.options.get_open_option_positions()

    for open_pos in open_option_positions:
        if open_pos['option_id'] == order_info['rh_option_uuid']:
            log.append(
                "Existing position info before any trades: \n" + json.dumps(open_pos))
            current_position_size = int(float(open_pos['quantity']))
            opening_position_size = current_position_size

    log.append(f'Opening position size: {opening_position_size}')
    log.append(f'Current position size: {current_position_size}')

    final_position_size = current_position_size - int(order_info['quantity'])
    # in case the quantity to sell is greater than the total owned
    # this will close the position to zero
    # and stop the sell orders from failing
    if final_position_size < 0:
        final_position_size = 0
        log.append(
            f'Tradebox order is asking to sell more positions than are currently held in account. final_position_size revised to {final_position_size} (should read 0).')
    log.append(f'Calculated final position size: {final_position_size}')

    order_cancel_ids = []

    while (current_position_size > final_position_size) and (number_of_trades_placed < order_info['max_order_attempts']):
        remaining_quantity = current_position_size - final_position_size
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
            log.append(f'Cancelling order ID {order_result["id"]}.')
            res = r.orders.cancel_option_order(order_result['id'])
            log.append(f'Result of cancellation: {json.dumps(res)}')
            order_cancel_ids.append(order_result['id'])
        except:
            pass

        time.sleep(3)

        # check current position status
        position_still_exists = False
        open_option_positions = r.options.get_open_option_positions()
        log.append(
            f'Updated raw position info after trade #{number_of_trades_placed}: \n\n {open_option_positions}')
        for open_pos in open_option_positions:
            if open_pos['option_id'] == order_info['rh_option_uuid']:
                current_position_size = int(float(open_pos['quantity']))
                position_still_exists = True
        if position_still_exists == False:
            current_position_size = 0
        log.append(
            f'Updated open option position quantity: {current_position_size}')

    time.sleep(1)

    # make sure all orders are actually cancelled at conclusion
    log.append(f'Cancelling {len(order_cancel_ids)} orders for safety.')
    for cancel_id in order_cancel_ids:
        try:
            log.append(f'Cancelling order ID {cancel_id}.')
            r.orders.cancel_option_order(order_result['id'])
        except:
            pass
        time.sleep(5)
    log.append('Cancelled all order IDs.')

    # log trade metrics
    open_option_positions = r.options.get_open_option_positions()
    for open_pos in open_option_positions:
        if open_pos['option_id'] == order_info['rh_option_uuid']:
            actual_closing_position_size = int(float(open_pos['quantity']))
    log.append(f'Opening position size: {opening_position_size}')
    log.append(f'Goal final position size: {final_position_size}')
    log.append(f'Actual closing position size: {actual_closing_position_size}')
    log.append(f'Final number of trades placed: {number_of_trades_placed}')


# postponed


def execute_limit_buy_order():
    pass

# postponed


def execute_limit_sell_order():
    pass


def cancel_all_robinhood_orders():
    login()
    r.orders.cancel_all_option_orders()
