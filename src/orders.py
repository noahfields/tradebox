import logging
import time

import robin_stocks.robinhood as r

import config
import database

logger = logging.getLogger(__name__)

def create_trigger_option_order(
        active: int,
        execute_only_after_id: int,
        execution_deactivates_order_id: int,
        buy_or_sell: str,
        credit_or_debit: str,
        symbol: str,
        strike: float,
        call_or_put: str,
        expiration_date: str,
        market_or_limit: str,
        limit_price: float,
        quantity: int,
        message_on_success: str,
        message_on_failure: str,
        max_order_attempts: int,
        emergency_order_fill_on_failure: int,
	):

        # "trigger_order_id_pk": "SERIAL PRIMARY KEY",
        # "active": "INTEGER",
        # "epoch_time_created_at": "REAL",
        # "executed": "INTEGER DEFAULT 0",
        # "execute_only_after_id": "INTEGER",
        # "execution_deactivates_order_id": "INTEGER",
        # "buy_or_sell": "TEXT",
        # "credit_or_debit": "TEXT",
        # "symbol": "TEXT",
        # "strike": "REAL",
        # "call_or_put": "TEXT",
        # "expiration_date": "TEXT",
        # "rh_option_uuid": "TEXT",
        # "market_or_limit": "TEXT",
        # "limit_price": "REAL",
        # "quantity": "INTEGER",
        # "message_on_success": "TEXT",
        # "message_on_failure": "TEXT",
        # "below_tick": "REAL",
        # "above_tick": "REAL",
        # "cutoff_price": "REAL",
        # "max_order_attempts": "INTEGER",
        # "emergency_order_fill_on_failure": "INTEGER",
	
    try:
        r.login(config.ROBINHOOD_USERNAME, config.ROBINHOOD_PASSWORD)
        r.get_option_instrument_data(symbol, expiration_date, strike, call_or_put)
    except Exception as e:
        logger.exception(f"Issue fetching option instrument data: {e}", stack_info=True)
        return None
    
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
        active=active,
        epoch_time_created_at=time.time(),
        executed=0,
        execute_only_after_id=execute_only_after_id,
        execution_deactivates_order_id=execution_deactivates_order_id,
        buy_or_sell=buy_or_sell,
        credit_or_debit=credit_or_debit,
        symbol=symbol,
        strike=strike,
        call_or_put=call_or_put,
        expiration_date=expiration_date,
        rh_option_uuid=rh_option_uuid,
        market_or_limit=market_or_limit,
        limit_price=limit_price,
        quantity=quantity,
        message_on_success=message_on_success,
        message_on_failure=message_on_failure,
        below_tick=below_tick,
        above_tick=above_tick,
        cutoff_price=cutoff_price,
        max_order_attempts=max_order_attempts,
        emergency_order_fill_on_failure=emergency_order_fill_on_failure,
    )

    msg = 'Successfully created order for ' \
        + f'{buy_or_sell} {quantity} {symbol}, {expiration_date}, {strike}, {call_or_put}.'
    logger.info(msg)
	
