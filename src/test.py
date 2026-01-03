import robin_stocks.robinhood as r

r.login('noahfields@gmail.com', 'cRU2mbMa2eL8PgF')
res = r.get_all_open_option_orders()
print(res)