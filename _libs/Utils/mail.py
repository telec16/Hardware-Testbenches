import smtplib
from typing import List

try:
    from __creds import GOOGLE
except ImportError:
    from Utils.__creds import GOOGLE


def simple_mail_sender(to: List[str], subject: str, body: str):
    """Send a mail using the caly's google account
    
    :param to: a list of string that contains one or more addresses
    :param subject: the subject of the message
    :param body: the body of the message
    :return: a dictionary, with one entry for each recipient that was refused. Each entry contains a tuple of the SMTP
        error code and the accompanying error message sent by the server. (More info at smtplib.sendmail)
    """

    email_text = f"""\
From: <{GOOGLE.user}>
To: <{">, <".join(to)}>
Subject: {subject}

{body}
"""

    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.ehlo()
    server.login(GOOGLE.user, GOOGLE.password)
    err = server.sendmail(GOOGLE.password, to, email_text.encode('UTF-8'))
    server.close()

    return err


if __name__ == "__main__":
    err = simple_mail_sender(["c.alytechnologies@gmail.com",
                              "c.alytechnologies+lol@gmail.com",
                              "c.alytech.nolo.gies@gmail.com"],
                             "HTRB Panic !", "It's fine actually ¯\\_(ツ)_/¯")
    print(err)

