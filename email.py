import smtplib
import ssl

import config

EMAIL = config.smtp_username
PASSWORD = config.smtp_password
SERVER = config.smtp_server
PORT = config.smtp_port
RECIPIENT = config.notifcation_address


def send_plaintext_email(message):
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(SERVER, PORT, context=context) as server:
        server.login(EMAIL, PASSWORD)
        # TODO: Send email here
        server.sendmail(EMAIL, RECIPIENT, message)
