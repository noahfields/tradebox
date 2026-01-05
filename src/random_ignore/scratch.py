import globals
import os

# Source - https://stackoverflow.com/a
# Posted by Bryan Oakley, modified by community. See post 'Timeline' for change history
# Retrieved 2025-12-28, License - CC BY-SA 4.0

print(globals.SRC_DIR)
print(globals.REPO_DIR)

try:
    os.makedirs(f"{globals.REPO_DIR}/logs")
except FileExistsError:
    print('dir exists already')