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
        "Attempt to fetch option instrument data for order:\n"
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

    msg = 'Successfully created order for ' \
        + f'{buy_or_sell} {quantity} {symbol}, {expiration_date}, {strike}, {call_or_put}.'
    logger.info(msg)
	
