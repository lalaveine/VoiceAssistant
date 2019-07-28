import pickle
import os.path
from email.mime.text import MIMEText
from email import policy
import email
import base64
from datetime import datetime
import time

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from definitions import CONFIG_DIR

# If modifying these scopes, delete the file token.pickle.
SCOPE = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.compose']
CREDENTIALS_PATH = os.path.join(CONFIG_DIR, 'credentials.json')
PICKLE_PATH = os.path.join(CONFIG_DIR, 'token.pickle.mail')

class VAMailGoogle:
    creds = None
    service = None
    sender = 'mfb.eugene@gmail.com'

    def __init__(self):
        if os.path.exists(PICKLE_PATH):
            with open(PICKLE_PATH, 'rb') as token:
                self.creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_PATH, SCOPE)
                self.creds = flow.run_local_server()
            # Save the credentials for the next run
            with open(PICKLE_PATH, 'wb') as token:
                pickle.dump(self.creds, token)

        self.service = build('gmail', 'v1', credentials=self.creds, cache_discovery=False)

    def create_email(self, to_whom, subject, message_text):
        message = MIMEText(message_text)
        message['to'] = to_whom
        message['from'] = self.sender
        message['subject'] = subject

        b64_bytes = base64.urlsafe_b64encode(message.as_bytes())
        b64_string = b64_bytes.decode()
        return {'raw': b64_string}

    def send_email(self, message):
        try:
            message = (self.service.users().messages().send(userId='me', body=message)
                       .execute())
            print('Message Id: %s' % message['id'])
            return message
        except:
            print('An error occurred')

    def list_messages(self, query):
        try:
            response = self.service.users().messages().list(userId='me', q=query).execute()
            messages = []
            if 'messages' in response:
                messages.extend(response['messages'])

            while 'nextPageToken' in response:
                page_token = response['nextPageToken']
                response = self.service.users().messages().list(userId='me', q=query, pageToken=page_token).execute()
                messages.extend(response['messages'])

            return messages
        except:
            print('An error occurred')

    def list_labels(self):
        try:
            response = self.service.users().labels().list(userId='me').execute()
            labels = response['labels']
            for label in labels:
                print('Label id: %s - Label name: %s' % (label['id'], label['name']))
            return labels
        except:
            print('An error occurred')

    # Example
    # unread = gmail.get_unread('in:inbox is:unread after:2019/06/01')
    def get_unread(self, query):
        response = self.service.users().messages().list(userId='me',
                                                   q=query).execute()
        messages = []
        if 'messages' in response:
            messages.extend(response['messages'])

        while 'nextPageToken' in response:
            page_token = response['nextPageToken']
            response = self.service.users().messages().list(userId='me', q=query,
                                                       pageToken=page_token).execute()
            messages.extend(response['messages'])

        result = []
        for message in messages:
            message = self.service.users().messages().get(userId='me', id=message['id'],
                                                           format='raw').execute()
            message_str = base64.urlsafe_b64decode(message['raw'].encode('utf-8')).decode("utf-8")
            mime_message = email.message_from_string(message_str, policy=policy.default)
            date = mime_message['date']
            from_whom = mime_message['from']
            if '<' in from_whom:
                from_whom = from_whom[:from_whom.index('<') - 1]

            result.append({
                    'From': from_whom,
                    'Subject': mime_message['subject'],
                    'Date': date[date.index(',') + 2:],
                    'id': mime_message['id']
                })
        return result


    def get_message_by_id(self, msg_id):
        try:
            message = self.service.users().messages().get(userId='me', id=msg_id, format='raw').execute()

            message_str = base64.urlsafe_b64decode(message['raw'].encode('utf-8')).decode("utf-8")
            mime_message = email.message_from_string(message_str, policy=policy.default)

            body = ""
            if mime_message.is_multipart():
                for part in mime_message.walk():
                    ctype = part.get_content_type()
                    cdispo = str(part.get('Content-Disposition'))

                    # skip any text/plain (txt) attachments
                    if ctype == 'text/plain' and 'attachment' not in cdispo:
                        body = part.get_payload(decode=True).decode("utf-8")  # decode
                        break
            # not multipart - i.e. plain text, no attachments, keeping fingers crossed
            else:
                body = mime_message.get_payload(decode=True).decode("utf-8")

            return body

        except:
            print('An error occurred')



if __name__ == '__main__':
    gmail = VAMailGoogle()
    unread = gmail.get_unread('in:inbox is:unread after:2019/06/01')
    print(unread)

    # id: 16b1f1f8dd32cdec
    # msg = gmail.get_message_by_id('16b1f1f8dd32cdec')
    # print(msg)
