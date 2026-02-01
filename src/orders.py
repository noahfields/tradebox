import datetime
import json
import logging
from socket import close
import time
import uuid

import robin_stocks.robinhood as r

import config
import database
import log
import pushover

logger = logging.getLogger(__name__)


def robinhood_login():
    """Logs into Robinhood using credentials from config."""
    try:
        r.login(config.ROBINHOOD_USERNAME, config.ROBINHOOD_PASSWORD)
        logger.info("Successfully logged into Robinhood.")
    except Exception as e:
        logger.exception(f"Failed to log into Robinhood: {e}", stack_info=True)


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
        max_mark_order_attempts: int,
        max_spread_order_attempts: int,
        emergency_order_fill_on_failure: bool,
        trigger_order_uuid: str,
	):
    logger.info("Begin creating trigger order.")

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
    logger.info(f"Instrument data fetch result: {instrument_data}")


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
        robinhood_option_uuid = instrument_data["id"]
        below_tick = instrument_data["min_ticks"]["below_tick"]
        above_tick = instrument_data["min_ticks"]["above_tick"]
        cutoff_price = instrument_data["min_ticks"]["cutoff_price"]


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
        robinhood_option_uuid,
        quantity,
        message_on_success,
        message_on_failure,
        below_tick,
        above_tick,
        cutoff_price,
        max_mark_order_attempts,
        max_spread_order_attempts,
        emergency_order_fill_on_failure,
        trigger_order_uuid,
    )

    msg = "Successfully created trigger order for " \
        + f"{buy_or_sell} {quantity} {symbol}, {expiration_date}, {strike}, {call_or_put}."
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
        max_mark_order_attempts: int,
        max_spread_order_attempts: int,
        emergency_order_fill_on_failure: bool
	):
    logger.info("Begin creating bracket order.")

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
    logger.info(f"Instrument data fetch result: {instrument_data}")


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
        robinhood_option_uuid = instrument_data["id"]
        below_tick = instrument_data["min_ticks"]["below_tick"]
        above_tick = instrument_data["min_ticks"]["above_tick"]
        cutoff_price = instrument_data["min_ticks"]["cutoff_price"]


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

    msg = "Successfully created bracket order for " \
        + f"{buy_or_sell} {quantity} {symbol}, {expiration_date}, {strike}, {call_or_put}."
    logger.info(msg)


def create_trailing_sell_option_order(
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
    message_on_success: str,
    message_on_failure: str,
    max_mark_order_attempts: int,
    max_spread_order_attempts: int,
    emergency_order_fill_on_failure: bool, 
    percent_from_high_sell_trigger: float,
    sell_at_specific_price: float,
    purchase_price: float,
	):
    logger.info("Begin creating trailing order: {symbol} {expiration_date} {strike} {call_or_put}.")

    logger.info(
        "Attempt to fetch option instrument data for trailing order:\n"
        f"{symbol} {expiration_date} {strike} {call_or_put}"
    )
    try:
        instrument_data = r.get_option_instrument_data(symbol, expiration_date, strike, call_or_put)
    except Exception as e:
        logger.exception(f"Issue fetching option instrument data: {e}", stack_info=True)
    logger.info(f"Instrument data fetch result: {instrument_data}")


    if instrument_data is None:
        logger.info(
            "r.get_option_instrument_data("
            f"{symbol}, {expiration_date}, {strike}, {call_or_put}) "
            "returned None. Option likely does not exist. "
            "Possible invalid symbol, strike, expiration date, and/or type (call/put). " 
            "Exiting create_trailing_option_order()."
        )
    else:
        robinhood_option_uuid = instrument_data["id"]
        below_tick = instrument_data["min_ticks"]["below_tick"]
        above_tick = instrument_data["min_ticks"]["above_tick"]
        cutoff_price = instrument_data["min_ticks"]["cutoff_price"]


    database.insert_trailing_sell_order(
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

    logger.info(
        "Successfully created trailing sell order for "
        f"{quantity} {symbol}, {expiration_date}, {strike}, {call_or_put}."
    )


# order dict could be any of the following:
# trigger_option_orders (as sell, determined by caller
# bracket_sell_option_orders
# trailing_sell_option_orders
def execute_market_sell(order: dict, runner_name: str, order_description: str) -> None:
    order_log = log.OrderLogger(
        symbol=order["symbol"],
        expiration_date=order["expiration_date"],
        strike=order["strike"],
        quantity=order["quantity"],
        buy_or_sell="sell",
        credit_or_debit="credit",
        description=order_description
    )
    order_log.log(f"Executing sell order. Order details: \n{order}")

    logger.info(f"Executing sell order. Order details: \n{order}", extra={"runner": runner_name})

    # log timestamp
    start_timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    logger.info(
        f"Begin execute_market_sell for order at {start_timestamp}. Order info:\n{order}", 
        extra={"runner": runner_name}
    )

    # trade progress information
    trade_progress_info = { 
        "number_of_trades_placed": 0,
        "opening_position_size": None,
        "current_position_size": None,
        "goal_final_position_size": None,
        "actual_closing_position_size": None,
        "max_order_attempts": order["max_order_attempts"],
        "remaining_quantity_to_execute": None,
    }

    # establish initial position information
    robinhood_reported_current_position_size = None
    open_option_positions = r.options.get_open_option_positions()
    for open_pos in open_option_positions:
        if open_pos["option_id"] == order["robinhood_option_uuid"]:
            logger.info(
                "Existing position info before any trades: \n"
                + f"{json.dumps(open_pos)}",
                extra={"runner": runner_name}
            )
            robinhood_reported_current_position_size = int(float(open_pos["quantity"]))


    # Exit if position is not found (e.g. probably don't own it)
    # Otherwise set up current and opening position size
    if robinhood_reported_current_position_size == None:
        logger.info(
            "No open position found for order # "
            f"{order['order_id_pk']}, RH option ID: {order['robinhood_option_uuid']}.\n"
            "Exiting market sell order.",
            extra={"runner": runner_name}
        )
        return
    else:
        trade_progress_info["current_position_size"] = robinhood_reported_current_position_size
        trade_progress_info["opening_position_size"] = robinhood_reported_current_position_size
    logger.info(
        f"Opening position size: {trade_progress_info['opening_position_size']}", 
        extra={"runner": runner_name}
    )
    logger.info(
        f"Current position size: {trade_progress_info['current_position_size']}", 
        extra={"runner": runner_name}
    )

    # Calculate goal_final_position_size
    trade_progress_info["goal_final_position_size"] = trade_progress_info["opening_position_size"] - int(order["quantity"])

    # In case the quantity to sell is greater than the total owned,
    # this will close the position to zero
    # and stop the sell orders from failing.
    if trade_progress_info["goal_final_position_size"] < 0:
        trade_progress_info["goal_final_position_size"] = 0
        logger.info(
            "Tradebox order is asking to sell more positions than are "
            "currently held in account. goal_final_position_size revised to "
            f"{trade_progress_info['goal_final_position_size']} (should read 0).",
            extra={"runner": runner_name}
        )
    logger.info(
        f"Goal final position size: {trade_progress_info['goal_final_position_size']}",
        extra={"runner": runner_name}
    )

    # Collect order IDs to cancel at conclusion
    order_cancel_ids = []

    mark_price_run = None
    while (trade_progress_info["current_position_size"] > trade_progress_info["goal_final_position_size"]) and (trade_progress_info["number_of_trades_placed"] < trade_progress_info["max_order_attempts"]):
        msg = (
            "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
            f"SELL MARKET: ORDER NUMBER {trade_progress_info['number_of_trades_placed'] + 1} "
            f"OF MAXIMUM {trade_progress_info['max_order_attempts']}"
            "\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        )
        logger.info(msg, extra={"runner": runner_name})

        # Calculate remaining quantity to sell
        trade_progress_info["remaining_quantity_to_execute"] = trade_progress_info["current_position_size"] - trade_progress_info["goal_final_position_size"]
        logger.info(
            f"Remaining quantity to sell: {trade_progress_info['remaining_quantity_to_execute']}", 
            extra={"runner": runner_name}
        )

        # Get Robinhood option market data
        option_market_data = r.options.get_option_market_data_by_id(order["robinhood_option_uuid"])[0]
        logger.info(f"Current raw market data: {json.dumps(option_market_data)}", extra={"runner": runner_name})
        if mark_price_run == None:
            this_order_sell_price = float(option_market_data["mark_price"])
            mark_price_run = True
        else:
            this_order_sell_price = float(option_market_data["bid_price"])
        if this_order_sell_price == 0.0:
            this_order_sell_price = 0.1

        # log qty and bid price
        msg = (
            "Attempting to sell\n"
            f"{trade_progress_info['remaining_quantity_to_execute']} options at {str(this_order_sell_price)}"
        )
        logger.info(msg, extra={"runner": runner_name})

        # Place order
        order_result = r.orders.order_sell_option_limit(
            "close",
            "credit",
            this_order_sell_price,
            order["symbol"],
            trade_progress_info["remaining_quantity_to_execute"],
            order["expiration_date"],
            order["strike"],
            optionType=order["call_or_put"],
            timeInForce="gtc",
        )
        logger.info(f"Robinhood order result dump:\n {json.dumps(order_result)}")

        # Iterate number of trades placed
        trade_progress_info["number_of_trades_placed"] += 1
        logger.info(f"Number of trades placed: {trade_progress_info['number_of_trades_placed']}")

        # Pause for order execution
        time.sleep(2)

        # Cancel order after pause
        logger.info(f"Cancelling order ID {order_result['id']}.")
        try:
            res = r.orders.cancel_option_order(order_result["id"])
            logger.info(f"Order ID {order_result['id']} cancelled.")
        except:
            msg = (
                f"Error cancelling {order_result['id']}.\n"
                f"Robinhood order cancellation result data: \n{json.dumps(res)}"
            )
            logger.info(msg)
        # Add order to cleanup list
        order_cancel_ids.append(order_result["id"])

        # Wait for positions to update on RH servers
        time.sleep(3)

        # Update position information
        position_still_exists = False
        open_option_positions = r.options.get_open_option_positions()
        msg = (
            "Updated raw position info after trade:\n"
            f"{json.dumps(open_option_positions)}"
        )
        logger.info(msg, extra={"runner": runner_name})
        for open_pos in open_option_positions:
            if open_pos["option_id"] == order["robinhood_option_uuid"]:
                trade_progress_info["current_position_size"] = int(float(open_pos["quantity"]))
                position_still_exists = True
        if position_still_exists == False:
            trade_progress_info["current_position_size"] = 0
        logger.info(
            f"Updated current position size: {trade_progress_info['current_position_size']}", 
            extra={"runner": runner_name}
        )

    time.sleep(3)

    #
    # TRADE REPORTING 
    # EMERGENCY SELL
    # CLEANUP
    #

    # Establish final position information
    open_option_positions = r.options.get_open_option_positions()
    for open_pos in open_option_positions:
        if open_pos["option_id"] == order["robinhood_option_uuid"]:
            trade_progress_info["current_position_size"] = int(float(open_pos["quantity"]))
            trade_progress_info["actual_closing_position_size"] = int(float(open_pos["quantity"]))
    logger.info(f"Opening position size: {trade_progress_info['opening_position_size']}", extra={"runner": runner_name})
    logger.info(f"Current position size: {trade_progress_info['current_position_size']}", extra={"runner": runner_name})
    logger.info(f"Goal final position size: {trade_progress_info['goal_final_position_size']}", extra={"runner": runner_name})
    logger.info(f"Actual closing position size: {trade_progress_info['actual_closing_position_size']}", extra={"runner": runner_name})
    logger.info(f"Final number of trades placed: {trade_progress_info['number_of_trades_placed']}", extra={"runner": runner_name})
    # build initial message report
    email_message_part_one = (
        f"SELLExd#{order['order_id']}"
        f"{order['symbol']}{order['call_or_put']}"
        f"{order['expiration_date']}{order['strike']}"
        f"Cur{trade_progress_info['current_position_size']}"
        f"St{trade_progress_info['opening_position_size']}"
        f"Gl{trade_progress_info['goal_final_position_size']}"
    )
    logger.info(email_message_part_one)

    # Emergency fill if goal quantity not met
    if bool(int(order["emergency_order_fill_on_failure"])) is True:
        logger.info("Emergency fill enabled.")
        if isinstance(trade_progress_info["actual_closing_position_size"], int) and (trade_progress_info["actual_closing_position_size"] > trade_progress_info["goal_final_position_size"]):
            logger.info("Emergency fill executing.")
            quantity_to_sell = trade_progress_info["actual_closing_position_size"] - trade_progress_info["goal_final_position_size"]
            execute_sell_emergency_fill(order, quantity_to_sell, runner_name, email_message_part_one)
        else:
            logger.info("Emergency fill not required based on current position size.")
            logger.info(email_message_part_one)
            pushover.send_notification(email_message_part_one)
            logger.info("Email/text notification sent.")
    else:
        logger.info("No emergency fill ordered.")
        logger.info(email_message_part_one)
        pushover.send_notification(email_message_part_one)
        logger.info("Email/text notification sent.")


    # Re-cancel all orders at conclusion
    logger.info(f"Cancelling {len(order_cancel_ids)} orders for safety.")
    for cancel_id in order_cancel_ids:
        try:
            logger.info(f"Cancelling order ID {cancel_id}.")
            res = r.orders.cancel_option_order(order_result["id"])
        except:
            logger.info(
                f"Error cancelling order ID {cancel_id}.\n"
                f"Robinhood cancel_option_order res dump: \n{json.dumps(res)}",
                extra={"runner": runner_name}
            )
        time.sleep(4)

    logger.info("Cancelled all order IDs from execute_market_sell_order.")
    logger.info("Completed execute_market_sell_order.")


def execute_sell_emergency_fill(order: dict, quantity_to_sell: int, runner_name: str, prepend_message: str = "") -> None:
    msg = (
        f"Emergency sell: trying to sell {quantity_to_sell} qty "
        f"{order['symbol']} | {order['call_or_put']} | "
        f"{order['strike']} | {order['expiration_date']}"
    )
    logger.info(msg, extra={"runner": "emergency_sell"})

    option_market_data = r.options.get_option_market_data_by_id(order["robinhood_option_uuid"])[0]

    bid_price = round(float(option_market_data['bid_price']), 2)
    logger.info(f"Emergency sell: bid price {bid_price}", extra={"runner": runner_name})

    # 50% discount
    sell_price = round(bid_price / 2, 2)
    logger.info(f"Emergency sell: 50% discount sell price {sell_price}", extra={"runner": runner_name})

    # find nearest tick (just using .05 cents here)
    sell_price = round(round(sell_price * 10) / 10, 2)
    if sell_price == 0:  # in case the option has bottomed out
        sell_price = 0.01

    logger.info(f"Emergency sell: revised sell price {sell_price}", extra={"runner": runner_name})

    order_result = r.orders.order_sell_option_limit(
        "close",
        "credit",
        sell_price,
        order["symbol"],
        quantity_to_sell,
        order["expiration_date"],
        order["strike"],
        optionType=order["call_or_put"],
        timeInForce="gtc",
    )

    logger.info(
        f"Emergency sell: RH data sell order result: {json.dumps(order_result)}", 
        extra={"runner": runner_name}
    )

    time.sleep(5)

    try:
        res = r.orders.cancel_option_order(order_result["id"])
    except:
        logger.info("Error cancelling order after emergency sell fill.", extra={"runner": runner_name})
        res = ""
    msg = (
        "Emergency order made. Cancelled order after 20 seconds. "
        f"Result of cancellation: {json.dumps(res)}"
    )
    logger.info(msg, extra={"runner": runner_name})
    time.sleep(2)

    open_option_positions = r.options.get_open_option_positions()
    after_emergency_position_quantity = "none"
    for open_pos in open_option_positions:
        if open_pos["option_id"] == order["robinhood_option_uuid"]:
            after_emergency_position_quantity = int(float(open_pos["quantity"]))

    msg = (
        "emergency sell: quantity after emergency sell "
        f"{after_emergency_position_quantity}"
    )
    logger.info(msg, extra={"runner": runner_name})

    msg = (
        f"ESf{after_emergency_position_quantity}"
    )
    logger.info(msg, extra={"runner": runner_name})

    pushover.send_notification(f"{prepend_message} {msg}")
    logger.info("Email/text notification sent. Emergency fill executed.", extra={"runner": runner_name})