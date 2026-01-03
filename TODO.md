##### Execution Structure
- systemd services:
    - runners.py
    - flask server
- logs/loggers:
    - runners
    - flask server
    - textual console
- console.py:
    - mobile version:
        easy buttons to cancel orders and close positions
    - desktop verison

##### Project formatting:
- no comments, readable without
- typehints for parameters and return values
- globals are capitalized
- log calls should be one at a time to prevent multiple notifications back to back

##### Logger levels:
- DEBUG: Expected milestones to track code if a problem occurs in development, or temporary problem fixing
- INFO: API call info
- WARNING: Should never occur but won't break app
- ERROR: Should never occur, might break app, sent to notifications
- CRITICAL: Should never occur, will probably or definitely break app, sent to notifications
---
##### To-do list:
- [ ] Review database.py
    - [x] pre-function formatting
    - [x] review get_database_connection
    - [x] review execute_set_database_query
    - [x] review drop_table
    - [x] review populate_runners_table

- [ ] Review runner function
    - [ ] Format create_database_function
    - [ ] 

- [ ] Figure out how to add trigger conditions on an order if position hits a certain loss or gain % 





order ability
trailing orders to follow price up
bracket order:
    - sell when up x% (market order)
    - sell when down x% (market order)
alert orders from TV
