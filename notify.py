"""Provides the ability to send plaintext email message reporting."""

import smtplib
import ssl
import traceback

import config
import log

USEREMAIL = config.SMTP_USERNAME
PASSWORD = config.SMTP_PASSWORD
SERVER = config.SMTP_SERVER
PORT = config.SMTP_PORT
RECIPIENT = config.NOTIFICATION_ADDRESS

def log_traceback(ex):
    tb_lines = traceback.format_exception(ex.__class__, ex, ex.__traceback__)
    tb_text = ''.join(tb_lines)
    log.append(tb_text)


def send_plaintext_email(message):
    try:
        context = ssl.create_default_context()

        with smtplib.SMTP_SSL(SERVER, PORT, context=context) as server:
            server.login(USEREMAIL, PASSWORD)
            # TODO: Send email here
            server.sendmail(USEREMAIL, RECIPIENT, message)
    except Exception as ex:
        log.append('There was an issue sending plaintext email. Logging full traceback.')
        log_traceback(ex)

