import smtplib
import imaplib
import ssl
import email

# Import the email modules we'll need
from email.message import EmailMessage

smtp_server = "smtp.mail.me.com"
starttls_port = 587
smtp_login = ""

imap_server = "imap.mail.me.com"
imap_port = 993
imap_login = ""

password = ""


def send_email(receiver_email, message_text, message_subject):
    # Default ssl context
    context = ssl.create_default_context()

    message = EmailMessage()
    message.set_content(message_text)
    message['Subject'] = message_subject
    message['From'] = smtp_login
    message['To'] = receiver_email

    try:
        server = smtplib.SMTP(smtp_server, starttls_port)
        server.ehlo()  # Can be omitted
        server.starttls(context=context)  # Secure the connection
        server.ehlo()  # Can be omitted
        server.login(smtp_login, password)
        server.send_message(message)
    except Exception as e:
        # Print any error messages to stdout
        print(e)
    finally:
        server.quit()

def get_email():
    mail = imaplib.IMAP4_SSL(imap_server, imap_port)
    mail.login(imap_login, password)
    mail.list()
    mail.select("INBOX", readonly=True)

    status, data = mail.search(None, 'ALL')
    ids = data[0]  # data is a list.
    id_list = ids.split()  # ids is a space separated string
    latest_email_id = id_list[-1]  # get the latest
    status, data = mail.fetch(latest_email_id, '(RFC822)')

    raw_email = data[0][1]
    message = email.message_from_bytes(raw_email)

    print(message['From'])
    print(message['Subject'])
    print(message.get_payload()[0])

    mail.close()
    mail.logout()


if __name__ == '__main__':
    # receiver_mail = ""
    # send_email(receiver_mail, "text", "Subject")
    # print("message sent")
    get_email()


