import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from definitions import CONFIG_DIR

# If modifying these scopes, delete the file token.pickle.
SCOPE = ['https://www.googleapis.com/auth/calendar.events']
CREDENTIALS_PATH = os.path.join(CONFIG_DIR, 'credentials.json')
PICKLE_PATH = os.path.join(CONFIG_DIR, 'token.pickle.calendar')


class VACalendarGoogle:
    creds = None
    service = None

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

        self.service = build('calendar', 'v3', credentials=self.creds, cache_discovery=False)

    def list_calendars(self):
        page_token = None
        while True:
            calendar_list = self.service.calendarList().list(pageToken=page_token).execute()
            for calendar_list_entry in calendar_list['items']:
                print(calendar_list_entry['summary'])
            page_token = calendar_list.get('nextPageToken')
            if not page_token:
                break

    # Takes argument day in datetime.date format
    def get_events_on_a_day(self, day):
        day_start = day.isoformat() + "T00:00:00+03:00"
        day_finish = day.isoformat() + "T23:59:59+03:00"
        page_token = None
        events_list = []
        while True:
            events = self.service.events().list(calendarId='primary', timeMin=day_start, timeMax=day_finish, pageToken=page_token).execute()
            for event in events['items']:
                events_list.append({
                    'Summary': event['summary'],
                    'Link': event['htmlLink'],
                    'Start': event['start'],
                    'End': event['end']
                })
            page_token = events.get('nextPageToken')
            if not page_token:
                break
        return events_list

    def get_event(self):
        pass

    def remove_event(self, event_id):
        self.service.events().delete(calendarId='primary', eventId=event_id).execute()

    def add_event(self, summary, start_time, end_time, send_invites, description=None, attendees=None, reminders=None):
        event = {}
        event['summary'] = summary
        event['description'] = description
        event['start'] = {
                'dateTime': start_time,
                'timeZone': 'Europe/Moscow',
            }
        event['end'] = {
                # 'dateTime': '2019-06-10T19:00:00+03:00',
                'dateTime': end_time,
                'timeZone': 'Europe/Moscow',
            }
        event['attendees'] = attendees
        event['reminders'] = {
                'useDefault': True
            }

        event = self.service.events().insert(calendarId='primary', sendUpdates=send_invites, body=event).execute()
        print('Event created: %s' % (event.get('htmlLink')))


if __name__ == '__main__':
    gcal = VACalendarGoogle()
    # gcal.list_calendars()
    # gcal.add_event()
