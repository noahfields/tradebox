"""Provides interface functions to Robinhood API
and helper functions to actions on the local database.
"""

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
    res = r.login(
        config.ROBINHOOD_USERNAME,
        config.ROBINHOOD_PASSWORD,
        expiresIn=config.ROBINHOOD_SESSION_EXPIRES_IN,
    )

    msg = f'tradeapi.login(): Logged in to Robinhood: \n{res}'
    log.append(msg)


def logout() -> None:
    try:
        r.logout()
    except Exception as e:
        log.append(f"Exception raised in tradeapi.logout(): {e}")

    try:
        home_dir = os.path.expanduser("~")
        robinhood_tokens_dir = os.path.join(home_dir, ".tokens")
        robinhood_creds_file = "robinhood.pickle"
        pickle_path = os.path.join(robinhood_tokens_dir, robinhood_creds_file)
        os.remove(pickle_path)
    except FileNotFoundError as e:
        log.append(f"Exception raised in tradeapi.logout(): {e}")

    log.append("Logged out of Robinhood.")


def create_order(
        buy_sell: str,
        symbol: str,
        expiration_date: str,
        strike: float,
        call_put: str,
        quantity: int,
        market_limit: str,
        emergency_order_fill_on_failure: bool,
        active: bool,
        message_on_success: str,
        message_on_failure: str,
        execute_only_after_id: int,
        execution_deactivates_order_id: int,
        max_order_attempts: int,
        limit_price: float = 0.0
    ) -> None:
    msg = 'tradeapi.create_order(): Begin creating order.'
    log.append(msg)


    msg = 'Attempt to fetch option instrument data for order:\n' \
        + f'{symbol} {expiration_date} {strike} {call_put}'
    log.append(msg)
    instrument_data = r.options.get_option_instrument_data(
        symbol, expiration_date, strike, call_put
    )
    msg = f'Instrument data fetch result: {instrument_data}'
    log.append(msg)


    if instrument_data is None:
        msg = (
            'tradeapi.create_order(): r.options.get_option_instrument_data('
            + f'{symbol}, {expiration_date}, {strike}, {call_put}) '
            + 'returned None. Option likely does not exist. '
            + 'Possible invalid symbol, strike, expiration date, and/or type (call/put). ' \
            + 'Exiting tradeapi.create_order().'
        )
        log.append(msg)
        return
    else:
        rh_option_uuid = instrument_data['id']
        below_tick = instrument_data['min_ticks']['below_tick']
        above_tick = instrument_data['min_ticks']['above_tick']
        cutoff_price = instrument_data['min_ticks']['cutoff_price']


    db.insert_order(
        buy_sell,
        symbol,
        expiration_date,
        strike,
        call_put,
        quantity,
        market_limit,
        emergency_order_fill_on_failure,
        active,
        message_on_success,
        message_on_failure,
        execute_only_after_id,
        execution_deactivates_order_id,
        max_order_attempts,
        limit_price,
        rh_option_uuid,
        below_tick,
        above_tick,
        cutoff_price,
    )


    msg = 'Successfully created order for ' \
        + f'{buy_sell} {quantity} {symbol}, {expiration_date}, {strike}, {call_put}.'
    log.append(msg)


def execute_order(order_id: int) -> None:
    msg = f'Begin tradeapi.py:execute_order() for order {order_id}.'
    log.append(msg)

    login()

    # get order information from local database
    try:
        order_info = db.get_order_series(order_id)
    except KeyError:
        msg = f'Looks like order #{order_id} does not exist. Aborting tradeapi.execute_order({order_id}).'
        log.append(msg)
        return


    # abort if inactive
    if bool(int(order_info['active'])) is False:
        msg = f'tradeapi.execute_order(): order #{order_id} is not active. Aborting execution.'
        log.append(msg)
        return

    # abort if executed
    if bool(int(order_info['executed'])) is True:
        msg = f'tradeapi.execute_order(): order #{order_id} has already executed. Aborting execution.'
        log.append(msg)
        return


    # continue execution 
    # if prequisitve order
    # exists and has executed
    msg = f'Checking to see if prerequisite order #"{order_info['execute_only_after_id']}" exists.'
    log.append(msg)
    if db.order_exists(order_info['execute_only_after_id']) is True:
        if db.get_order_executed_status(order_info['execute_only_after_id']) is True:
            msg = f'Prerequisite order exists and has executed.\n' \
            + f'Continuing execution of order #{order_id}.'  
            log.append(msg)
        else:
            msg = f'Prerequisite order exists but has not executed.\n' \
            + f'Cancelling execution of order #{order_id}.'
            log.append(msg)
            return
    else:
        msg = f'Prerequisite order #{order_info["execute_only_after_id"]} does not exist. ' \
            + f'Continuing execution of order #{order_id}.'
        log.append(msg)
        pass
    

    # mark trade as executed
    db.set_order_executed_status(order_id, True)
    log.append(f'Updated order number {order_id} as executed.')

    # set order as inactive
    db.set_order_active_status(order_id, False)
    log.append(f'Updated order number {order_id} as inactive.')

    # deactivate check
    msg = f'Attempting to deactivate order #{order_info["execution_deactivates_order_id"]}. (execution deactivates order id#)'
    log.append(msg)
    db.set_order_active_status(order_info['execution_deactivates_order_id'], False)


    # select correct order function
    # and execute order
    if order_info['buy_sell'] == 'buy' and order_info['market_limit'] == 'market':
        execute_market_buy_order(order_info)
    elif order_info['buy_sell'] == 'sell' and order_info['market_limit'] == 'market':
        execute_market_sell_order(order_info)
    else:
        msg = 'No valid order type selected.\n' \
            + f'buy/sell: {order_info["buy_sell"]}\n' \
            + f'market/limit: {order_info["market_limit"]}'
        log.append(msg)


    msg = f'Completed tradeapi.execute_order({order_id}).'
    log.append(msg)


def get_option_instrument_data(
    symbol: str, call_put: str, strike: float, expiration_date: str
) -> tuple[float, float, float, str]:
    data = r.options.get_option_instrument_data(
        symbol, expiration_date, strike, call_put
    )

    below_tick = data["min_ticks"]["below_tick"]
    above_tick = data["min_ticks"]["above_tick"]
    cutoff_price = data["min_ticks"]["cutoff_price"]
    option_uuid = data["id"]

    return below_tick, above_tick, cutoff_price, option_uuid


def execute_market_buy_order(order_info: pd.Series) -> None:
    # log timestamp
    start_timestamp = datetime.datetime.now().strftime('%H:%M:%S')
    msg = f'Begin execute_market_buy_order for order #{order_info["order_id"]} at {start_timestamp}.'
    log.append(msg)


    # log order info
    log.append(f'Tradebox order info: \n{order_info.to_string()}')


    # trade progress information
    trade_progress_info = { 
        'number_of_trades_placed': 0,
        'opening_position_size': 'undefined',
        'current_position_size': 'undefined',
        'goal_final_position_size': 'undefined',
        'actual_closing_position_size': 'undefined',
        'max_order_attempts': order_info['max_order_attempts'],
        'remaining_quantity_to_execute': 'undefined',
    }


    # establish initial position information
    robinhood_reported_current_position_size = None
    open_option_positions = r.options.get_open_option_positions()
    for open_pos in open_option_positions:
        if open_pos['option_id'] == order_info['rh_option_uuid']:
            msg = (
                'Existing position info before any trades: \n'
                + f'{json.dumps(open_pos)}'
            )
            log.append(msg)
            robinhood_reported_current_position_size = int(float(open_pos['quantity']))

    if robinhood_reported_current_position_size is None:
        trade_progress_info['current_position_size'] = 0
        trade_progress_info['opening_position_size'] = 0
    else:
        trade_progress_info['current_position_size'] =  robinhood_reported_current_position_size
        trade_progress_info['opening_position_size'] =  robinhood_reported_current_position_size

    log.append(f'Opening position size: {trade_progress_info["current_position_size"]}')
    log.append(f'Current position size: {trade_progress_info["opening_position_size"]}')


    # establish goal position size
    trade_progress_info['goal_final_position_size'] = trade_progress_info['current_position_size'] + int(order_info['quantity'])

    msg = 'Calculated goal final position size: ' \
        + f'{trade_progress_info["goal_final_position_size"]}'
    log.append(msg)


    # list of order IDs to cancel during order cleanup
    order_cancel_ids = []


    # MAIN ORDER LOOP
    while trade_progress_info['current_position_size'] < trade_progress_info['goal_final_position_size'] and trade_progress_info['number_of_trades_placed'] < trade_progress_info['max_order_attempts']:
        msg = '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n' \
            + f'BUY MARKET: ORDER NUMBER {trade_progress_info["number_of_trades_placed"] + 1} ' \
            + f'OF MAXIMUM {trade_progress_info["max_order_attempts"]}' \
            + '\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
        log.append(msg)
        

        # Calculate remaining quantity to buy
        trade_progress_info['remaining_quantity_to_execute'] = trade_progress_info['goal_final_position_size'] - trade_progress_info['current_position_size']
        msg = f'Remaining quantity to buy: {trade_progress_info["remaining_quantity_to_execute"]}'
        log.append(msg)

        # Get Robinhood option market data
        option_market_data = r.options.get_option_market_data_by_id(order_info['rh_option_uuid'])[0]
        log.append(f'Current raw market data: {json.dumps(option_market_data)}')

        # log qty and ask price
        msg = (
            'Attempting to buy\n'
            + f'{trade_progress_info["remaining_quantity_to_execute"]} options at {str(float(option_market_data["ask_price"]))}'
        )
        log.append(msg)

        # place order
        order_result = r.orders.order_buy_option_limit(
            'open',
            'debit',
            option_market_data['ask_price'],
            order_info['symbol'],
            trade_progress_info['remaining_quantity_to_execute'],
            order_info['expiration_date'],
            order_info['strike'],
            optionType=order_info['call_put'],
            timeInForce='gtc',
        )
        log.append(f'RH order result dump:\n {json.dumps(order_result)}')

        # Iterate number of trades placed
        trade_progress_info['number_of_trades_placed'] += 1
        log.append(f'Number of trades placed: {trade_progress_info["number_of_trades_placed"]}')

        # Pause for order execution
        time.sleep(2)

        # Cancel order after pause
        log.append(f'Cancelling order ID {order_result["id"]}.')
        try:
            res = r.orders.cancel_option_order(order_result['id'])
            log.append(f'Order ID {order_result["id"]} cancelled.')
        except:
            msg = f'Error cancelling {order_result["id"]}.\n' \
                + f'RH order cancellation result data: \n{json.dumps(res)}'
            log.append(msg)
        # Add order to cleanup list
        order_cancel_ids.append(order_result['id'])

        # Wait for positions to update on RH servers
        time.sleep(3)

        # Update position information
        open_option_positions = r.options.get_open_option_positions()
        msg = (
            'Updated raw position info after trade:\n'
            + f'{json.dumps(open_option_positions)}'
        )
        log.append(msg)
        for open_pos in open_option_positions:
            if open_pos['option_id'] == order_info['rh_option_uuid']:
                trade_progress_info['current_position_size'] = int(float(open_pos['quantity']))
        msg = f'Updated current position qty: {trade_progress_info["current_position_size"]}'
        log.append(msg)

    time.sleep(3)

    #
    # TRADE REPORTING 
    # EMERGENCY BUY
    # CLEANUP
    #

    # Establish final position information
    open_option_positions = r.options.get_open_option_positions()
    for open_pos in open_option_positions:
        if open_pos['option_id'] == order_info['rh_option_uuid']:
            trade_progress_info['current_position_size'] = int(float(open_pos['quantity']))
            trade_progress_info['actual_closing_position_size'] = trade_progress_info['current_position_size']
    log.append(f'Opening position size: {trade_progress_info["opening_position_size"]}')
    log.append(f'Current position size: {trade_progress_info["current_position_size"]}')
    log.append(f'Goal final position size: {trade_progress_info["goal_final_position_size"]}')
    log.append(f'Actual closing position size: {trade_progress_info["actual_closing_position_size"]}')
    log.append(f'Final number of trades placed: {trade_progress_info["number_of_trades_placed"]}')

    if trade_progress_info['actual_closing_position_size'] == 'undefined':
        quantity_bought = 0
    else:
        quantity_bought = trade_progress_info['actual_closing_position_size'] - trade_progress_info['opening_position_size']


    # build message to email/text
    # message_part_one will be sent alone
    # if emergency order fill is not activated
    # otherwise it will be prepended to the emergency order email/text
    email_message_part_one = (
        f'Exd#{order_info["order_id"]}'
        + f'{order_info["symbol"]}{order_info["call_put"]}'
        + f'{order_info["expiration_date"]}{order_info["strike"]}'
        + f'Cur{trade_progress_info["actual_closing_position_size"]}'
        + f'St{trade_progress_info["opening_position_size"]}'
        + f'Gl{trade_progress_info["goal_final_position_size"]}'
    )

    log.append(email_message_part_one)


    # Emergency fill if goal quantity not met
    if trade_progress_info['current_position_size'] < trade_progress_info['goal_final_position_size']:
        log.append('tradeapi.execute_market_buy_order did not fill completely.')
        if bool(order_info['emergency_order_fill_on_failure']) is True:
            log.append('Emergency buy fill is activated. Executing emergency fill.')
            quantity_to_buy =  trade_progress_info['goal_final_position_size'] - trade_progress_info['current_position_size']
            execute_buy_emergency_fill(order_info, quantity_to_buy, email_message_part_one)
        else:
            log.append('No emergency fill is ordered. Goal quantity met was not met, but emegency fill was not set to execute.')
            notify.send_plaintext_email(email_message_part_one)
            log.append('Email/text notification sent.')
    else:
        log.append('No emergency fill required based on position quantity.')
        notify.send_plaintext_email(email_message_part_one)
        log.append('Email/text notification sent.')


    # Re-cancel all orders at conclusion
    log.append(f'Cancelling {len(order_cancel_ids)} orders for safety.')
    for cancel_id in order_cancel_ids:
        try:
            log.append(f'Cancelling order ID {cancel_id}.')
            res = r.orders.cancel_option_order(order_result['id'])
        except:
            msg = f'Error cancelling order ID {cancel_id}.\n' \
                + f'RH cancel_option_order res dump: \n{json.dumps(res)}'
            log.append(msg)
        time.sleep(4)

    log.append('Cancelled all order IDs from execute_market_buy_order.')
    log.append('Completed execute_market_buy_order.')


def execute_market_sell_order(order_info: pd.Series) -> None:
    # log timestamp
    start_timestamp = datetime.datetime.now().strftime('%H:%M:%S')
    msg = f'Begin execute_market_sell_order for order #{order_info["order_id"]} at {start_timestamp}.'
    log.append(msg)


    # log order info
    log.append('Tradebox order info: \n' + order_info.to_string())


    # trade progress information
    trade_progress_info = { 
        'number_of_trades_placed': 0,
        'opening_position_size': 'undefined',
        'current_position_size': 'undefined',
        'goal_final_position_size': 'undefined',
        'actual_closing_position_size': 'undefined',
        'max_order_attempts': order_info['max_order_attempts'],
        'remaining_quantity_to_execute': 'undefined',
    }


    # establish initial position information
    robinhood_reported_current_position_size = None
    open_option_positions = r.options.get_open_option_positions()
    for open_pos in open_option_positions:
        if open_pos['option_id'] == order_info['rh_option_uuid']:
            msg = (
                'Existing position info before any trades: \n'
                + f'{json.dumps(open_pos)}'
            )
            log.append(msg)
            robinhood_reported_current_position_size = int(float(open_pos['quantity']))


    # Exit if position is not found (e.g. probably don't own it)
    # Otherwise set up current and opening position size
    if robinhood_reported_current_position_size is None:
        msg = (
            'No open position found for order # '
            + f'{order_info["order_id"]}, RH option ID: {order_info["rh_option_uuid"]}.\n'
            + 'Exiting market sell order.'
        )
        log.append(msg)
        return
    else:
        trade_progress_info['current_position_size'] = robinhood_reported_current_position_size
        trade_progress_info['opening_position_size'] = robinhood_reported_current_position_size
    log.append(f'Opening position size: {trade_progress_info["opening_position_size"]}')
    log.append(f'Current position size: {trade_progress_info["current_position_size"]}')


    # Calculate goal_final_position_size
    trade_progress_info['goal_final_position_size'] = trade_progress_info['opening_position_size'] - int(order_info['quantity'])


    # In case the quantity to sell is greater than the total owned,
    # this will close the position to zero
    # and stop the sell orders from failing.
    if trade_progress_info['goal_final_position_size'] < 0:
        trade_progress_info['goal_final_position_size'] = 0
        msg = (
            'Tradebox order is asking to sell more positions than are '
            + 'currently held in account. goal_final_position_size revised to '
            + f'{trade_progress_info["goal_final_position_size"]} (should read 0).'
        )
        log.append(msg)
    log.append(f'Goal final position size: {trade_progress_info["goal_final_position_size"]}')


    # Collect order IDs to cancel at conclusion
    order_cancel_ids = []


    while (trade_progress_info['current_position_size'] > trade_progress_info['goal_final_position_size']) and (trade_progress_info['number_of_trades_placed'] < trade_progress_info['max_order_attempts']):
        msg = '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n' \
            + f'SELL MARKET: ORDER NUMBER {trade_progress_info["number_of_trades_placed"] + 1} ' \
            + f'OF MAXIMUM {trade_progress_info["max_order_attempts"]}' \
            + '\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
        log.append(msg)
        

        # Calculate remaining quantity to sell
        trade_progress_info['remaining_quantity_to_execute'] = trade_progress_info['current_position_size'] - trade_progress_info['goal_final_position_size']
        msg = f'Remaining quantity to sell: {trade_progress_info["remaining_quantity_to_execute"]}'
        log.append(msg)

        # Get Robinhood option market data
        option_market_data = r.options.get_option_market_data_by_id(order_info['rh_option_uuid'])[0]
        log.append(f'Current raw market data: {json.dumps(option_market_data)}')

        # log qty and bid price
        msg = (
            'Attempting to sell\n'
            + f'{trade_progress_info["remaining_quantity_to_execute"]} options at {str(float(option_market_data["bid_price"]))}'
        )
        log.append(msg)
        
        # Place order
        order_result = r.orders.order_sell_option_limit(
            'close',
            'credit',
            option_market_data['bid_price'],
            order_info['symbol'],
            trade_progress_info['remaining_quantity_to_execute'],
            order_info['expiration_date'],
            order_info['strike'],
            optionType=order_info['call_put'],
            timeInForce='gtc',
        )
        log.append(f'RH order result dump:\n {json.dumps(order_result)}')

        # Iterate number of trades placed
        trade_progress_info['number_of_trades_placed'] += 1
        log.append(f'Number of trades placed: {trade_progress_info["number_of_trades_placed"]}')

        # Pause for order execution
        time.sleep(2)

        # Cancel order after pause
        log.append(f'Cancelling order ID {order_result["id"]}.')
        try:
            res = r.orders.cancel_option_order(order_result['id'])
            log.append(f'Order ID {order_result["id"]} cancelled.')
        except:
            msg = (
                f'Error cancelling {order_result["id"]}.\n'
                + f'RH order cancellation result data: \n{json.dumps(res)}'
            )
            log.append(msg)
        # Add order to cleanup list
        order_cancel_ids.append(order_result['id'])

        # Wait for positions to update on RH servers
        time.sleep(3)

        # Update position information
        position_still_exists = False
        open_option_positions = r.options.get_open_option_positions()
        msg = (
            'Updated raw position info after trade:\n'
            + f'{json.dumps(open_option_positions)}'
        )
        log.append(msg)
        for open_pos in open_option_positions:
            if open_pos['option_id'] == order_info['rh_option_uuid']:
                trade_progress_info['current_position_size'] = int(float(open_pos['quantity']))
                position_still_exists = True
        if position_still_exists is False:
            trade_progress_info['current_position_size'] = 0
        msg = f'Updated current position size: {trade_progress_info["current_position_size"]}'
        log.append(msg)

    time.sleep(3)

    #
    # TRADE REPORTING 
    # EMERGENCY SELL
    # CLEANUP
    #

    # Establish final position information
    open_option_positions = r.options.get_open_option_positions()
    for open_pos in open_option_positions:
        if open_pos['option_id'] == order_info['rh_option_uuid']:
            trade_progress_info['current_position_size'] = int(float(open_pos['quantity']))
            trade_progress_info['actual_closing_position_size'] = int(float(open_pos['quantity']))
    log.append(f'Opening position size: {trade_progress_info["opening_position_size"]}')
    log.append(f'Current position size: {trade_progress_info["current_position_size"]}')
    log.append(f'Goal final position size: {trade_progress_info["goal_final_position_size"]}')
    log.append(f'Actual closing position size: {trade_progress_info["actual_closing_position_size"]}')
    log.append(f'Final number of trades placed: {trade_progress_info["number_of_trades_placed"]}')

    # build initial message report
    email_message_part_one = (
        f'Exd#{order_info["order_id"]}'
        + f'{order_info["symbol"]}{order_info["call_put"]}'
        + f'{order_info["expiration_date"]}{order_info["strike"]}'
        + f'Cur{trade_progress_info["current_position_size"]}'
        + f'St{trade_progress_info["opening_position_size"]}'
        + f'Gl{trade_progress_info["goal_final_position_size"]}'
    )
    log.append(email_message_part_one)


    # Emergency fill if goal quantity not met
    if bool(int(order_info['emergency_order_fill_on_failure'])) is True:
        log.append('Emergency fill enabled.')
        if isinstance(trade_progress_info['actual_closing_position_size'], int) and (trade_progress_info['actual_closing_position_size'] > trade_progress_info['goal_final_position_size']):
            log.append('Emergency fill executing.')
            quantity_to_sell = trade_progress_info['actual_closing_position_size'] - trade_progress_info['goal_final_position_size']
            execute_sell_emergency_fill(order_info, quantity_to_sell, email_message_part_one)
        else:
            log.append('Emergency fill not required based on current position size.')
            log.append(email_message_part_one)
            notify.send_plaintext_email(email_message_part_one)
            log.append('Email/text notification sent.')
    else:
        log.append('No emergency fill ordered.')
        log.append(email_message_part_one)
        notify.send_plaintext_email(email_message_part_one)
        log.append('Email/text notification sent.')


    # Re-cancel all orders at conclusion
    log.append(f'Cancelling {len(order_cancel_ids)} orders for safety.')
    for cancel_id in order_cancel_ids:
        try:
            log.append(f'Cancelling order ID {cancel_id}.')
            res = r.orders.cancel_option_order(order_result['id'])
        except:
            msg = f'Error cancelling order ID {cancel_id}.\n' \
                + f'RH cancel_option_order res dump: \n{json.dumps(res)}'
            log.append(msg)
        time.sleep(4)

    log.append('Cancelled all order IDs from execute_market_sell_order.')
    log.append('Completed execute_market_sell_order.')


def cancel_all_robinhood_orders() -> None:
    r.orders.cancel_all_option_orders()


def get_console_open_robinhood_positions() -> pd.DataFrame:
    open_positions = r.options.get_open_option_positions()

    display_positions = []

    for open_position in open_positions:
        instrument_data = r.options.get_option_instrument_data_by_id(
            open_position["option_id"]
        )
        quantity = int(float(open_position["quantity"]))
        symbol = open_position["chain_symbol"]
        average_price = round(float(open_position["average_price"]), 2)
        strike = round(float(instrument_data["strike_price"]), 2)
        call_put = instrument_data["type"]
        expiration_date = instrument_data["expiration_date"]

        market_data = r.options.get_option_market_data_by_id(
            open_position["option_id"]
        )[0]

        adjusted_mark_price = round(float(market_data["adjusted_mark_price"]), 2)

        display_position = {
            "symbol": symbol,
            "call_put": call_put,
            "expiration_date": expiration_date,
            "strike": strike,
            "quantity": quantity,
            "average_price": average_price,
            "current_mark": adjusted_mark_price,
        }

        display_positions.append(display_position)

    positions_dataframe = pd.DataFrame(display_positions)
    return positions_dataframe


def execute_sell_emergency_fill(order_info: pd.Series, quantity_to_sell: int, prepend_message: str = '') -> None:
    msg = (
        f'Emergency sell: trying to sell {quantity_to_sell} qty '
        + f'{order_info["symbol"]} {order_info["call_put"]} '
        + f'{order_info["strike"]} {order_info["expiration_date"]}'
    )
    log.append(msg)

    option_market_data = r.options.get_option_market_data_by_id(order_info['rh_option_uuid'])[0]

    bid_price = round(float(option_market_data['bid_price']), 2)
    log.append(f'Emergency sell: bid price {bid_price}')

    # 50% discount
    sell_price = round(bid_price / 2, 2)
    log.append(f'Emergency sell: 50% discount sell price {sell_price}')

    # find nearest tick (just using .05 cents here)
    sell_price = round(round(sell_price * 10) / 10, 2)
    if sell_price == 0:  # in case the option has bottomed out
        sell_price = 0.01

    log.append(f'Emergency sell: revised sell price {sell_price}')

    order_result = r.orders.order_sell_option_limit(
        'close',
        'credit',
        sell_price,
        order_info['symbol'],
        quantity_to_sell,
        order_info['expiration_date'],
        order_info['strike'],
        optionType=order_info['call_put'],
        timeInForce='gtc',
    )

    log.append(f'Emergency sell: RH data sell order result: {json.dumps(order_result)}')

    time.sleep(20)

    try:
        res = r.orders.cancel_option_order(order_result['id'])
    except:
        log.append('Error cancelling order after emergency sell fill.')
        res = ''
    msg = (
        'Emergency order made. Cancelled order after 20 seconds. '
        + f'Result of cancellation: {json.dumps(res)}'
    )
    log.append(msg)

    time.sleep(2)

    open_option_positions = r.options.get_open_option_positions()
    after_emergency_position_quantity = 'err or 0'
    for open_pos in open_option_positions:
        if open_pos['option_id'] == order_info['rh_option_uuid']:
            after_emergency_position_quantity = int(float(open_pos['quantity']))

    msg = (
        'emergency sell: quantity after emergency sell '
        + f'{after_emergency_position_quantity}'
    )
    log.append(msg)

    msg = (
        f'ESq{after_emergency_position_quantity}'
    )
    log.append(f'{prepend_message} {msg}')

    notify.send_plaintext_email(f'{prepend_message} {msg}')
    log.append('Email/text notification sent. Emergency fill executed.')


def execute_buy_emergency_fill(order_info: pd.Series, quantity_to_buy: int, prepend_message: str = '') -> None:
    msg = (
        f'emergency buy: trying to buy {quantity_to_buy} '
        + f'{order_info["symbol"]} {order_info["call_put"]} '
        + f'{order_info["strike"]} {order_info["expiration_date"]}'
    )
    log.append(msg)


    option_market_data = r.options.get_option_market_data_by_id(order_info['rh_option_uuid'])[0]

    ask_price = round(float(option_market_data['ask_price']), 2)
    log.append(f'emergency buy: bid price {ask_price}')

    # 50% higher buy price than ask price, add on 5 cents for rounding
    buy_price = round((ask_price * 1.5) + 0.05, 2)
    log.append(f'emergency buy: 50% higher buy price plus 5 cents {buy_price}')

    # find nearest tick (just using .05 cents here)
    buy_price = round(round(buy_price * 10) / 10, 2)
    log.append(f'emergency buy: rounded buy price {buy_price}')


    order_result = r.orders.order_buy_option_limit(
        'close',
        'debit',
        buy_price,
        order_info['symbol'],
        quantity_to_buy,
        order_info['expiration_date'],
        order_info['strike'],
        optionType=order_info['call_put'],
        timeInForce='gtc',
    )

    log.append(f'Emergency buy order result: {json.dumps(order_result)}')

    time.sleep(10)

    try:
        res = r.orders.cancel_option_order(order_result['id'])
    except:
        res = ''
        log.append('Error cancelling order after emergency buy fill. Account may have insufficient funds.')
    msg = (
        'Emergency buy order made. Order did not execute or was cancelled order after 10 seconds.\n' 
        + f'Result of cancellation: {json.dumps(res)}'
    )
    log.append(msg)

    time.sleep(2)

    open_option_positions = r.options.get_open_option_positions()
    after_emergency_position_quantity = None
    for open_pos in open_option_positions:
        if open_pos['option_id'] == order_info['rh_option_uuid']:
            after_emergency_position_quantity = int(float(open_pos['quantity']))

    msg = (
        'Emergency buy. Quantity after emergency buy: '
        + f'{after_emergency_position_quantity}'
    )
    log.append(msg)

    msg = (
        f'Eq{after_emergency_position_quantity}'
    )

    log.append(f'{prepend_message} {msg}')
    notify.send_plaintext_email(f'{prepend_message} {msg}')
    log.append('Email/text notification sent. Emergency buy fill executed.')
