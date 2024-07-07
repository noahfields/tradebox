# terminal entry system for tradebox
import pandas
import pyinputplus as pyip

import db
import tradeapi

menu_options = ['create order (c)', 'delete order (d)', 'delete all orders (da)',
                'cancel all robinhood orders direct (car)', 'login (li)',
                'logout (lo)', 'execute order # (e)', 'print https link for order (l)']


def create_order():
    buy_sell = pyip.inputStr(
        'buy/sell> ', blockRegexes=[r'.*'], allowRegexes=['buy', 'sell'])
    quantity = pyip.inputInt('quantity> ')
    call_put = pyip.inputStr(
        'call/put> ', blockRegexes=[r'.*'], allowRegexes=['call', 'put'])
    symbol = pyip.inputStr('symbol> ').upper()
    expiration_date = pyip.inputDate(
        'expiration_date> ', formats=['%Y-%m-%d']).strftime('%Y-%m-%d')
    strike = pyip.inputFloat('strike> ')
    market_limit = pyip.inputStr(
        'market/limit> ',
        blockRegexes=[r'.*'], allowRegexes=['market', 'limit'])

    limit_price = 0.0
    if market_limit == 'limit':
        limit_price = pyip.inputFloat('limit price> ')

    active = pyip.inputBool('order active? (True/False)> ')

    execute_only_after_id = pyip.inputInt(
        'execute only after order #> ', blank=True)
    execution_deactivates_order_id = pyip.inputInt(
        'execution deactivates order #> ', blank=True)
    message_on_success = pyip.inputStr('success msg> ', blank=True)
    message_on_failure = pyip.inputStr('failure msg> ', blank=True)
    max_order_attempts = pyip.inputInt('max order attempts (recommend 10)> ')

    tradeapi.create_order(buy_sell, symbol, expiration_date, strike, call_put,
                          quantity, market_limit, limit_price=limit_price,
                          message_on_success=message_on_success,
                          message_on_failure=message_on_failure,
                          execute_only_after_id=execute_only_after_id,
                          max_order_attempts=max_order_attempts,
                          execution_deactivates_order_id=execution_deactivates_order_id, active=active)


def delete_order():
    order_id = pyip.inputInt('order # to delete> ')
    db.delete_order(order_id)


def delete_all_orders():
    db.delete_all_orders()


def cancel_all_robinhood_orders():
    tradeapi.cancel_all_robinhood_orders()


def print_orders():
    orders = db.fetch_console_order_dataframe()
    print(orders.to_string())


def print_open_positions():
    res = tradeapi.get_console_open_robinhood_positions()
    print(res)


def print_http_link():
    order_id = pyip.inputInt('order #> ')
    print(f'https://noahtradebox.duckdns.org/orders/execute/{order_id}')


def execute_order():
    order_number = pyip.inputInt('execute order#> ')
    tradeapi.execute_order(order_number)


if __name__ == '__main__':
    # make sure tradebox is logged in
    tradeapi.login()

    db.create_orders_table()

    while True:
        print('TRADEBOX CONSOLE\n')

        try:
            print('OPEN POSITIONS')
            print_open_positions()
            print('\n')
        except:
            print("NOT LOGGED IN!!!")
            print("Not logged in. Could not print open option positions.")

        print('TRADEBOX ORDERS')
        print_orders()
        print('\nMenu:')

        for item in menu_options:
            print(item)

        menu_choice = input('> ')

        print('\n')

        if menu_choice == 'c':
            create_order()
        elif menu_choice == 'd':
            delete_order()
        elif menu_choice == 'da':
            delete_all_orders()
        elif menu_choice == 'car':
            cancel_all_robinhood_orders()
        elif menu_choice == 'li':
            tradeapi.login()
        elif menu_choice == 'lo':
            tradeapi.logout()
        elif menu_choice == 'e':
            execute_order()
        elif menu_choice == 'l':
            print_http_link()
        elif menu_choice == 'quit' or menu_choice == 'q':
            quit()
        elif menu_choice == 'exit':
            quit()
        elif menu_choice == '':
            pass
        else:
            print('Invalid selection.')

        print('\n\n')
