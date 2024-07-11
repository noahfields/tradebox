"""Provides the ability to send plaintext email message reporting."""
import smtplib
import ssl

import config

USEREMAIL = config.SMTP_USERNAME
PASSWORD = config.SMTP_PASSWORD
SERVER = config.SMTP_SERVER
PORT = config.SMTP_PORT
RECIPIENT = config.NOTIFICATION_ADDRESS


def send_plaintext_email(message):
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(SERVER, PORT, context=context) as server:
        server.login(USEREMAIL, PASSWORD)
        # TODO: Send email here
        server.sendmail(USEREMAIL, RECIPIENT, message)
