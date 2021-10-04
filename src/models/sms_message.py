import smtplib

from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from models.logger import Logger
from smtplib import SMTPServerDisconnected, SMTPNotSupportedError,\
                    SMTPSenderRefused

log = Logger.getInstance().getLogger()


class SMSMessage(object):
    """
    Send SMS messages.
    """

    def __init__(self, email, pas, sms_gateway,
                 smtp_server='smtp.gmail.com', smtp_port=587):
        self.email = email
        self.pas = pas
        self.sms_gateway = sms_gateway
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.start_email_server()

    def send_message(self, subject='', body=''):
        msg = MIMEMultipart()
        msg['From'] = self.email
        msg['To'] = self.sms_gateway
        msg['Subject'] = 'FPL Manager\n'
        msg.attach(MIMEText(body, 'plain'))
        sms = msg.as_string()

        try:
            self.server.sendmail(self.email, self.sms_gateway, sms)
            log.info("Notification sent")
        except (SMTPServerDisconnected, SMTPNotSupportedError,
                SMTPSenderRefused):
            log.info("SMTP server is disconnected, reconnect...")
            # self.server.starttls()
            # self.server.login(self.email, self.pas)
            self.start_email_server()
            self.server.sendmail(self.email, self.sms_gateway, sms)
            log.info("Notification sent")

    def start_email_server(self):
        # Start email server
        self.server = smtplib.SMTP(self.smtp_server,
                                   self.smtp_port)
        self.server.starttls()
        # TODO - Error check to make sure server started.
        self.server.login(self.email, self.pas)

    def kill_email_server(self):
        self.server.quit()