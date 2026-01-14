import datetime
import logging
import time
import uuid

import robin_stocks.robinhood as r

import config
import database

logger = logging.getLogger(__name__)

def create_trigger_option_order(
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
        strike: str,
        call_or_put: str,
        expiration_date: str,
        quantity: int,
        message_on_success: str,
        message_on_failure: str,
        max_order_attempts: int,
        emergency_order_fill_on_failure: bool,
        trigger_order_uuid: str,
	):
    logger.info('Begin creating trigger order.')

    logger.info(
        "Attempt to fetch option instrument data for trigger order:\n"
        f"{symbol} {expiration_date} {strike} {call_or_put}"
    )
    try:
        r.login(config.ROBINHOOD_USERNAME, config.ROBINHOOD_PASSWORD)
        instrument_data = r.get_option_instrument_data(symbol, expiration_date, strike, call_or_put)
    except Exception as e:
        logger.exception(f"Issue fetching option instrument data: {e}", stack_info=True)
        return None
    logger.info(f'Instrument data fetch result: {instrument_data}')


    if instrument_data is None:
        msg = (
            "r.get_option_instrument_data("
            f"{symbol}, {expiration_date}, {strike}, {call_or_put}) "
            "returned None. Option likely does not exist. "
            "Possible invalid symbol, strike, expiration date, and/or type (call/put). " 
            "Exiting orders.create_order()."
        )
        logger.info(msg)
        return
    else:
        rh_option_uuid = instrument_data['id']
        below_tick = instrument_data['min_ticks']['below_tick']
        above_tick = instrument_data['min_ticks']['above_tick']
        cutoff_price = instrument_data['min_ticks']['cutoff_price']


    database.insert_trigger_order(
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
        trigger_order_uuid,
    )

    msg = 'Successfully created trigger order for ' \
        + f'{buy_or_sell} {quantity} {symbol}, {expiration_date}, {strike}, {call_or_put}.'
    logger.info(msg)

def create_bracket_option_order(
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
        strike: str,
        call_or_put: str,
        expiration_date: str,
        quantity: int,
        high_sell_mark_price: float,
        low_sell_mark_price: float,
        message_on_success: str,
        message_on_failure: str,
        max_order_attempts: int,
        emergency_order_fill_on_failure: bool
	):
    logger.info('Begin creating bracket order.')

    logger.info(
        "Attempt to fetch option instrument data for bracket order:\n"
        f"{symbol} {expiration_date} {strike} {call_or_put}"
    )
    try:
        r.login(config.ROBINHOOD_USERNAME, config.ROBINHOOD_PASSWORD)
        instrument_data = r.get_option_instrument_data(symbol, expiration_date, strike, call_or_put)
    except Exception as e:
        logger.exception(f"Issue fetching option instrument data: {e}", stack_info=True)
        return None
    logger.info(f'Instrument data fetch result: {instrument_data}')


    if instrument_data is None:
        msg = (
            "r.get_option_instrument_data("
            f"{symbol}, {expiration_date}, {strike}, {call_or_put}) "
            "returned None. Option likely does not exist. "
            "Possible invalid symbol, strike, expiration date, and/or type (call/put). " 
            "Exiting orders.create_order()."
        )
        logger.info(msg)
        return
    else:
        rh_option_uuid = instrument_data['id']
        below_tick = instrument_data['min_ticks']['below_tick']
        above_tick = instrument_data['min_ticks']['above_tick']
        cutoff_price = instrument_data['min_ticks']['cutoff_price']


    database.insert_bracket_order(
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

    msg = 'Successfully created bracket order for ' \
        + f'{buy_or_sell} {quantity} {symbol}, {expiration_date}, {strike}, {call_or_put}.'
    logger.info(msg)

def create_trailing_option_order(
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
        strike: str,
        call_or_put: str,
        expiration_date: str,
        quantity: int,
        message_on_success: str,
        message_on_failure: str,
        max_order_attempts: int,
        emergency_order_fill_on_failure: bool,
        percent_from_high_sell_trigger: float,
        sell_at_specific_price: float,
        cost_basis: float
	):
    logger.info('Begin creating trailing order.')

    logger.info(
        "Attempt to fetch option instrument data for trailing order:\n"
        f"{symbol} {expiration_date} {strike} {call_or_put}"
    )
    try:
        r.login(config.ROBINHOOD_USERNAME, config.ROBINHOOD_PASSWORD)
        instrument_data = r.get_option_instrument_data(symbol, expiration_date, strike, call_or_put)
    except Exception as e:
        logger.exception(f"Issue fetching option instrument data: {e}", stack_info=True)
        return None
    logger.info(f'Instrument data fetch result: {instrument_data}')


    if instrument_data is None:
        msg = (
            "r.get_option_instrument_data("
            f"{symbol}, {expiration_date}, {strike}, {call_or_put}) "
            "returned None. Option likely does not exist. "
            "Possible invalid symbol, strike, expiration date, and/or type (call/put). " 
            "Exiting orders.create_order()."
        )
        logger.info(msg)
        return
    else:
        rh_option_uuid = instrument_data['id']
        below_tick = instrument_data['min_ticks']['below_tick']
        above_tick = instrument_data['min_ticks']['above_tick']
        cutoff_price = instrument_data['min_ticks']['cutoff_price']


    database.insert_trailing_order(
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

    msg = 'Successfully created trailing order for ' \
        + f'{buy_or_sell} {quantity} {symbol}, {expiration_date}, {strike}, {call_or_put}.'
    logger.info(msg)


def execute_market_sell(order):
    # log timestamp
    start_timestamp = datetime.datetime.now().strftime('%H:%M:%S')
    logger.info(f"Begin execute_market_sell for order at {start_timestamp}. Order info:\n{order}")

    # trade progress information
    trade_progress_info = { 
        "number_of_trades_placed": 0,
        "opening_position_size": "undefined",
        "current_position_size": "undefined",
        "goal_final_position_size": "undefined",
        "actual_closing_position_size": "undefined",
        "max_order_attempts": order["max_order_attempts"],
        "remaining_quantity_to_execute": "undefined",
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
            logger.info(msg)
            robinhood_reported_current_position_size = int(float(open_pos['quantity']))


    # Exit if position is not found (e.g. probably don't own it)
    # Otherwise set up current and opening position size
    if robinhood_reported_current_position_size is None:
        msg = (
            'No open position found for order # '
            + f'{order_info["order_id"]}, RH option ID: {order_info["rh_option_uuid"]}.\n'
            + 'Exiting market sell order.'
        )
        logger.info(msg)
        return
    else:
        trade_progress_info['current_position_size'] = robinhood_reported_current_position_size
        trade_progress_info['opening_position_size'] = robinhood_reported_current_position_size
    logger.info(f'Opening position size: {trade_progress_info["opening_position_size"]}')
    logger.info(f'Current position size: {trade_progress_info["current_position_size"]}')


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
        logger.info(msg)
    logger.info(f'Goal final position size: {trade_progress_info["goal_final_position_size"]}')


    # Collect order IDs to cancel at conclusion
    order_cancel_ids = []


    while (trade_progress_info['current_position_size'] > trade_progress_info['goal_final_position_size']) and (trade_progress_info['number_of_trades_placed'] < trade_progress_info['max_order_attempts']):
        msg = '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n' \
            + f'SELL MARKET: ORDER NUMBER {trade_progress_info["number_of_trades_placed"] + 1} ' \
            + f'OF MAXIMUM {trade_progress_info["max_order_attempts"]}' \
            + '\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
        logger.info(msg)
        

        # Calculate remaining quantity to sell
        trade_progress_info['remaining_quantity_to_execute'] = trade_progress_info['current_position_size'] - trade_progress_info['goal_final_position_size']
        msg = f'Remaining quantity to sell: {trade_progress_info["remaining_quantity_to_execute"]}'
        logger.info(msg)

        # Get Robinhood option market data
        option_market_data = r.options.get_option_market_data_by_id(order_info['rh_option_uuid'])[0]
        logger.info(f'Current raw market data: {json.dumps(option_market_data)}')
        this_order_sell_price = float(option_market_data['bid_price'])
        if this_order_sell_price == 0.0:
            this_order_sell_price = 0.1

        # log qty and bid price
        msg = (
            'Attempting to sell\n'
            + f'{trade_progress_info["remaining_quantity_to_execute"]} options at {str(this_order_sell_price)}'
        )
        logger.info(msg)
        
        # Place order
        order_result = r.orders.order_sell_option_limit(
            'close',
            'credit',
            this_order_sell_price,
            order_info['symbol'],
            trade_progress_info['remaining_quantity_to_execute'],
            order_info['expiration_date'],
            order_info['strike'],
            optionType=order_info['call_put'],
            timeInForce='gtc',
        )
        logger.info(f'RH order result dump:\n {json.dumps(order_result)}')

        # Iterate number of trades placed
        trade_progress_info['number_of_trades_placed'] += 1
        logger.info(f'Number of trades placed: {trade_progress_info["number_of_trades_placed"]}')

        # Pause for order execution
        time.sleep(2)

        # Cancel order after pause
        logger.info(f'Cancelling order ID {order_result["id"]}.')
        try:
            res = r.orders.cancel_option_order(order_result['id'])
            logger.info(f'Order ID {order_result["id"]} cancelled.')
        except:
            msg = (
                f'Error cancelling {order_result["id"]}.\n'
                + f'RH order cancellation result data: \n{json.dumps(res)}'
            )
            logger.info(msg)
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
        logger.info(msg)
        for open_pos in open_option_positions:
            if open_pos['option_id'] == order_info['rh_option_uuid']:
                trade_progress_info['current_position_size'] = int(float(open_pos['quantity']))
                position_still_exists = True
        if position_still_exists is False:
            trade_progress_info['current_position_size'] = 0
        msg = f'Updated current position size: {trade_progress_info["current_position_size"]}'
        logger.info(msg)

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
    logger.info(f'Opening position size: {trade_progress_info["opening_position_size"]}')
    logger.info(f'Current position size: {trade_progress_info["current_position_size"]}')
    logger.info(f'Goal final position size: {trade_progress_info["goal_final_position_size"]}')
    logger.info(f'Actual closing position size: {trade_progress_info["actual_closing_position_size"]}')
    logger.info(f'Final number of trades placed: {trade_progress_info["number_of_trades_placed"]}')

    # build initial message report
    email_message_part_one = (
        f'SELLExd#{order_info["order_id"]}'
        + f'{order_info["symbol"]}{order_info["call_put"]}'
        + f'{order_info["expiration_date"]}{order_info["strike"]}'
        + f'Cur{trade_progress_info["current_position_size"]}'
        + f'St{trade_progress_info["opening_position_size"]}'
        + f'Gl{trade_progress_info["goal_final_position_size"]}'
    )
    logger.info(email_message_part_one)


    # Emergency fill if goal quantity not met
    if bool(int(order_info['emergency_order_fill_on_failure'])) is True:
        logger.info('Emergency fill enabled.')
        if isinstance(trade_progress_info['actual_closing_position_size'], int) and (trade_progress_info['actual_closing_position_size'] > trade_progress_info['goal_final_position_size']):
            logger.info('Emergency fill executing.')
            quantity_to_sell = trade_progress_info['actual_closing_position_size'] - trade_progress_info['goal_final_position_size']
            execute_sell_emergency_fill(order_info, quantity_to_sell, email_message_part_one)
        else:
            logger.info('Emergency fill not required based on current position size.')
            logger.info(email_message_part_one)
            pushover.send_notification(email_message_part_one)
            logger.info('Email/text notification sent.')
    else:
        logger.info('No emergency fill ordered.')
        logger.info(email_message_part_one)
        pushover.send_notification(email_message_part_one)
        logger.info('Email/text notification sent.')


    # Re-cancel all orders at conclusion
    logger.info(f'Cancelling {len(order_cancel_ids)} orders for safety.')
    for cancel_id in order_cancel_ids:
        try:
            logger.info(f'Cancelling order ID {cancel_id}.')
            res = r.orders.cancel_option_order(order_result['id'])
        except:
            msg = f'Error cancelling order ID {cancel_id}.\n' \
                + f'RH cancel_option_order res dump: \n{json.dumps(res)}'
            logger.info(msg)
        time.sleep(4)

    logger.info('Cancelled all order IDs from execute_market_sell_order.')
    logger.info('Completed execute_market_sell_order.')