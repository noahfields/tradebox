NOT PRODUCTION READY - JULY 24, 2024
PLEASE DO NOT USE

Trade API and console for requests to the Robinhood Trade API.

For help setting up a server on Debian or Ubuntu:
https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-22-04


NOTES:
1) tradeapi requests can take a long time. You should set the timeout limit on gunicorn or other wsgi server to a high timeout limit. 10 minutes or 600 seconds is a good setting.
Example:
/home/username/tradeboxvenv/bin/gunicorn --timeout 600 --workers 3 --bind unix:tradebox.sock -m 007 wsgi:app
2) Please edit the config-default-must-rename.py contents to include your Robinhood username and password, SMTP email info and recipient information, and then rename the file to 'config.py'. Otherwise the Flask server and console.py will not run.