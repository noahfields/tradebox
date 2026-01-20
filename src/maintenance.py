import robin_stocks.robinhood as r
import config


def save_robinhood_api_data():
    res = r.login(config.ROBINHOOD_USERNAME, config.ROBINHOOD_PASSWORD)

    with open("robinhood_api_data.py", "w") as f:
        f.write("API_VERIFICATION_DEFAULT_KEYSETS = {\n")

        f.write('    "get_open_option_positions": {\n')
        res = r.get_open_option_positions()
        for key, value in res[0].items():
            f.write(f'        "{key}": "{value}",\n')
        f.write("    },\n")


        f.write('    "get_option_market_data_by_id": {\n')
        # get_option_market_data = r.get_option_market_data("IWM", "2026-03-20", 258, "call")[0]
        res = r.get_option_market_data_by_id("6e2980cb-87e9-45bc-abd8-b12508015a9f")
        for key, value in res[0].items():
            f.write(f'        "{key}": "{value}",\n')
        f.write("    },\n")


        f.write('    "get_option_instrument_data_by_id": {\n')
        res = r.get_option_instrument_data_by_id("6e2980cb-87e9-45bc-abd8-b12508015a9f")
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

