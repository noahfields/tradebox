import http.client, urllib

import config

def send_notification(msg):
    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
    urllib.parse.urlencode({
        "token": config.PUSHOVER_API_TOKEN, # Pushover API Token/Key (under "Your Applications")
        "user": config.PUSHOVER_USER_TOKEN, # Pushover User Key (available on main page on pushover.net)
        "message": msg,
    }), { "Content-type": "application/x-www-form-urlencoded" })
    res = conn.getresponse()