import json
import os
import traceback
import time

import pandas as pd
import robin_stocks.robinhood as r

import db
import notify
import log
import config


def login():
    r.login(config.ROBINHOOD_USERNAME,
            config.ROBINHOOD_PASSWORD, expiresIn='172800')


def logout():
    try:
        r.logout()
    except:
        pass
    home_dir = os.path.expanduser("~")
    data_dir = os.path.join(home_dir, ".tokens")
    creds_file = "robinhood.pickle"
    pickle_path = os.path.join(data_dir, creds_file)
    os.remove(pickle_path)


def create_order(buy_sell, symbol, expiration_date, strike, call_put, quantity,
                 market_limit, emergency_order_fill_on_failure, limit_price=0,
                 active=True, message_on_success='',
                 message_on_failure='', execute_only_after_id='',
                 execution_deactivates_order_id='', max_order_attempts=10):
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
                    above_tick, cutoff_price, limit_price, message_on_success, message_on_failure, execute_only_after_id, execution_deactivates_order_id, max_order_attempts, active, emergency_order_fill_on_failure)

    msg = f'Successfully created order for {buy_sell} {quantity} {
        symbol}, {expiration_date}, {strike}, {call_put}.'
    log.append(msg)


def execute_order(order_id):
    log.append(f'Begin execute_order for order {order_id}.')

    login()

    try:
        order_info = db.fetch_order_dataframe(order_id)
    except:
        msg = f'Looks like order #{
            order_id} does not exist. Aborting tradeapi.execute_order({order_id}).'
        print(msg)
        log.append(msg)
        return

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

    # mark trade as executed
    db.mark_order_executed(order_id)
    log.append(f'Marked order number {order_id} as executed.')

    # set order as inactive
    db.set_order_active_status(order_id, False)
    log.append(f'Marked order number {order_id} as inactive.')

    # deactivate check
    db.set_execution_deactivates_order_id(order_id)

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


def get_option_instrument_data(symbol, call_put, strike, expiration_date):
    login()

    data = r.options.get_option_instrument_data(
        symbol, expiration_date, strike, call_put)

    below_tick = data['min_ticks']['below_tick']
    above_tick = data['min_ticks']['above_tick']
    cutoff_price = data['min_ticks']['cutoff_price']
    option_uuid = data['id']

    return below_tick, above_tick, cutoff_price, option_uuid


def execute_market_buy_order(order_info):
    log.append(
        f'Begin execute_market_buy_order for order #{order_info["order_id"]}.')
    log.append("tradebox order info: \n" + order_info.to_string())

    # metrics to report at conclusion
    number_of_trades_placed = 0
    opening_position_size = 0
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
        time.sleep(4)
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

    # send email notification of trade
    quantity_bought = actual_closing_position_size - opening_position_size
    message = f'Tradebox executed order #{order_info["order_id"]}. Bought {quantity_bought} {order_info["symbol"]} {
        order_info["call_put"]} {order_info["expiration_date"]} {order_info["strike"]}. Current position size: {actual_closing_position_size}.'
    notify.send_plaintext_email(message)
    log.append('Email/text notification sent.')
    log.append(message)


def execute_market_sell_order(order_info):
    log.append(
        f'Begin execute_market_sell_order for order #{order_info["order_id"]}.')
    log.append("tradebox order info: \n" + order_info.to_string())

    # metrics to report at conclusion
    number_of_trades_placed = 0
    opening_position_size = 0
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

    # log trade metrics
    open_option_positions = r.options.get_open_option_positions()
    for open_pos in open_option_positions:
        if open_pos['option_id'] == order_info['rh_option_uuid']:
            actual_closing_position_size = int(float(open_pos['quantity']))
    log.append(f'Opening position size: {opening_position_size}')
    log.append(f'Goal final position size: {goal_final_position_size}')
    log.append(f'Actual closing position size: {actual_closing_position_size}')
    log.append(f'Final number of trades placed: {number_of_trades_placed}')

    # build initial message report
    if actual_closing_position_size != 'none':
        quantity_sold = opening_position_size - actual_closing_position_size
    message = f'Ex\'d ord{order_info["order_id"]}. Sold {quantity_sold} {order_info["symbol"]} {order_info["call_put"]} {
        order_info["expiration_date"]} {order_info["strike"]}. Cur pos: {actual_closing_position_size}.'

    log.append(message)

    if bool(int(order_info['emergency_order_fill_on_failure'])) == True:
        if actual_closing_position_size != 'none' and (actual_closing_position_size > goal_final_position_size):
            execute_sell_emergency_fill(
                order_info=order_info, quantity_to_sell=(actual_closing_position_size - goal_final_position_size), prepend_message=message)
    else:
        notify.send_plaintext_email(
            f'{message}. No emergency order submitted.')
        log.append('Email/text notification sent. No emergency fill.')

    # make sure all orders are actually cancelled at conclusion
    log.append(f'Cancelling {len(order_cancel_ids)} orders for safety.')
    for cancel_id in order_cancel_ids:
        try:
            log.append(f'Cancelling order ID {cancel_id}.')
            r.orders.cancel_option_order(order_result['id'])
        except:
            pass
        time.sleep(4)
    log.append('Cancelled all order IDs from main sell function.')


def execute_limit_buy_order():
    pass


def execute_limit_sell_order():
    pass


def cancel_all_robinhood_orders():
    login()
    r.orders.cancel_all_option_orders()


def get_console_open_robinhood_positions():
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


def execute_sell_emergency_fill(order_info='', quantity_to_sell=0, prepend_message=''):
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

    time.sleep(5)

    res = r.orders.cancel_option_order(order_result['id'])
    log.append(f'Emergency order made. Cancelling after 5 seconds. Result of cancellation: {
               json.dumps(res)}')

    time.sleep(3)

    open_option_positions = r.options.get_open_option_positions()
    after_emergency_position_quantity = 0
    for open_pos in open_option_positions:
        if open_pos['option_id'] == order_info['rh_option_uuid']:
            after_emergency_position_quantity = int(
                float(open_pos['quantity']))

    log.append(f'emergency sell: quantity after {
               after_emergency_position_quantity}')

    message = f'E.S.. new qty: {after_emergency_position_quantity}.'

    log.append(f'{prepend_message} {message}')
    notify.send_plaintext_email(f'{prepend_message} {message}')
    log.append('Email/text notification sent. Emergency fill executed.')


def execute_buy_emergency_fill(order_info='', quantity_to_buy=0):
    pass
