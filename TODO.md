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