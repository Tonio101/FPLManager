import heapq
import smtplib
from copy import deepcopy
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import (SMTPNotSupportedError, SMTPSenderRefused,
                     SMTPServerDisconnected)

from models.logger import Logger

log = Logger.getInstance().getLogger()


class SMSMessage(object):
    """
    Send SMS messages.
    """

    def __init__(
        self, email, pas, sms_gateway, smtp_server="smtp.gmail.com", smtp_port=587
    ):
        self.email = email
        self.pas = pas
        self.sms_gateway = sms_gateway
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.start_email_server()

    def send_message(self, subject="", body=""):
        msg = MIMEMultipart()
        msg["From"] = self.email
        msg["To"] = self.sms_gateway
        msg["Subject"] = "FPL Manager\n"
        msg.attach(MIMEText(body, "plain"))
        sms = msg.as_string()

        try:
            self.server.sendmail(self.email, self.sms_gateway, sms)
            log.info("Notification sent")
        except (SMTPServerDisconnected, SMTPNotSupportedError, SMTPSenderRefused):
            log.info("SMTP server is disconnected, reconnect...")
            # self.server.starttls()
            # self.server.login(self.email, self.pas)
            self.start_email_server()
            self.server.sendmail(self.email, self.sms_gateway, sms)
            log.info("Notification sent")

    def start_email_server(self):
        # Start email server
        self.server = smtplib.SMTP(self.smtp_server, self.smtp_port)
        self.server.starttls()
        # TODO - Error check to make sure server started.
        self.server.login(self.email, self.pas)

    def kill_email_server(self):
        self.server.quit()


class SmsNotifier(object):
    def __init__(self, data):
        self.sms_messages = []
        for sms in data["sms_info"]["sms"]:
            self.sms_messages.append(
                SMSMessage(
                    email=data["sms_info"]["email"],
                    pas=data["sms_info"]["passw"],
                    sms_gateway=sms["gateway"],
                    smtp_server=sms["server"],
                    smtp_port=sms["port"],
                )
            )

    def send(self, fpl_session, heap):
        message = self.build_sms_message(fpl_session, heap)
        log.debug(message)
        for sms in self.sms_messages:
            sms.send_message(body=message)

    def build_sms_message(self, fpl_session, heap):
        """[summary]

        Args:
            fpl_session ([type]): [description]
            heap ([type]): [description]

        Returns:
            [type]: [description]
        """
        winners = []
        losers = []
        draws = []
        rank = 1
        heap_copy = deepcopy(heap)
        curr_gw = fpl_session.get_current_gameweek()
        rank_str = ""
        outcome_str = ""

        while heap_copy:
            player = heapq.heappop(heap_copy).val

            name = player.get_name()
            if player.is_winner(curr_gw):
                winners.append(name)
            elif player.is_loser(curr_gw):
                losers.append(name)
            elif player.is_draw(curr_gw):
                draws.append(name)
            else:
                log.error("Invalid outcome")
                exit(2)

            rank_str += ("{0}. {1} " "{2}-{3}-{4} (W-D-L)\n").format(
                rank,
                name,
                player.get_total_win(),
                player.get_total_draw(),
                player.get_total_loss(),
            )
            rank += 1

        if len(winners) > 0:
            outcome_str += "Winners this week:\n"
            for winner in winners:
                outcome_str += ("{0}\n").format(winner)
        if len(draws) > 0:
            outcome_str += "Draw this week:\n"
            for draw in draws:
                outcome_str += ("{0}\n").format(draw)

        return ("{winners}\n{rank}\n").format(winners=outcome_str, rank=rank_str)
