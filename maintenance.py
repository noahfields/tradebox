import sys
import robin_stocks.robinhood as r
import config


def save_robinhood_api_data():
    res = r.login(config.ROBINHOOD_USERNAME, config.ROBINHOOD_PASSWORD)


    open_orders = r.get_all_open_option_orders()
    if len(open_orders) == 0:
        print('No open orders. Open an order in Robinhood to complete maintenance run.')
        sys.exit()


    open_positions = r.get_open_option_positions()
    if len(open_positions) == 0:
        print('No open positions. Open a position in Robinhood to complete maintenance run.')
        sys.exit()


    with open("robinhood_api_data.py", "w") as f:
        f.write("API_VERIFICATION_DEFAULT_KEYSETS = {\n")


        f.write('    "get_portfolio_profile": {\n')
        res = r.load_portfolio_profile()
        for key, value in res.items():
            f.write(f'        "{key}": "{value}",\n')
        f.write("    },\n")


        f.write('    "get_open_option_positions": {\n')
        res = r.get_open_option_positions()
        for key, value in res[0].items():
            f.write(f'        "{key}": "{value}",\n')
        f.write("    },\n")


        f.write('    "get_option_market_data_by_id": {\n')
        instrument_id = r.get_option_market_data("IWM", "2026-08-21", 275, "call")[0][0]["instrument_id"]
        res = r.get_option_market_data_by_id(instrument_id)
        for key, value in res[0].items():
            f.write(f'        "{key}": "{value}",\n')
        f.write("    },\n")


        f.write('    "get_option_instrument_data_by_id": {\n')
        res = r.get_option_instrument_data_by_id(instrument_id)
        for key, value in res.items():
            f.write(f'        "{key}": "{value}",\n')
        f.write("    },\n")


        f.write('    "get_all_open_option_orders": {\n')
        res = r.get_all_open_option_orders()
        for key, value in res[0].items():
            f.write(f'        "{key}": "{value}",\n')
        f.write("    },\n")

        f.write("}")


if __name__ == "__main__":
    save_robinhood_api_data()

