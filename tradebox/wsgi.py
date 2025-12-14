"""WSGI connection for Tradebox Flask server."""

from order_trigger_server import app

if __name__ == "__main__":
    app.run()