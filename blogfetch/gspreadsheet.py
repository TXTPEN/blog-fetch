from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from send_email import send_email

from blogfetch import BlogFetch

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None


LENGTH = 8
FLAG_APPROVED = 6
FLAG_SENT = 7

# If modifying these scopes, delete your previously saved credentials

# at ~/.credentials/sheets.googleapis.com-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Sheets API Python Quickstart'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    credential_dir = os.path.join('./', 'credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'google_spreadsheet.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

class Row():
    def __init__(self, range, row):
        self.range = range
        self.row = row
    def update(self, conn, row):
        conn._update([row], self.range)
    def set_sent(self, conn):
        self.row[FLAG_SENT] = u"1"
        conn._update([self.row], self.range)
    def is_sent(self):
        return self.row[FLAG_SENT] == '1'
    def is_approved(self):
        return self.row[FLAG_APPROVED] == '1'

    def __repr__(self):
        return "<class _Row, Approved: " + self.row[6] + ", Sent: " + self.row[7] + ">"

class DB():
    def __init__(self, sheet="Sheet1", spreadsheet_id='1nIoXjshnPZSG4zPGjHjMtmDn5XqARCIiDY03x3rxelg'):
        self.spreadsheet_id = spreadsheet_id
        self.sheet = sheet
        credentials = get_credentials()
        http = credentials.authorize(httplib2.Http())
        discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                        'version=v4')
        self.service = discovery.build('sheets', 'v4', http=http,
                                       discoveryServiceUrl=discoveryUrl)

    def _fetch(self, range):
        ret = []
        if range != '':
            range_name = self.sheet + '!' + range
        else:
            range_name = self.sheet

        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id, range=range_name).execute()
        values = result.get('values', [])

        if not values:
            return None
        else:
            for (i, row) in enumerate(values):
                while len(row) < LENGTH:
                    row.append(u"")
                obj = Row('A'+str(i+1)+":"+'H'+str(i+1), row)
                ret.append(obj)
            return ret[1:]

    def _update(self, values, range):
        if range != '':
            range_name = self.sheet + '!' + range
        else:
            range_name = self.sheet
        body = {'values': values}
        result = self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id, range=range_name,
                    body=body, valueInputOption="RAW").execute()

    def _append(self, values, range):
        if range != '':
            range_name = self.sheet + '!' + range
        else:
            range_name = self.sheet
        body = {'values': values}
        result = self.service.spreadsheets().values().append(
                    spreadsheetId=self.spreadsheet_id, range=range_name,
                    body=body, valueInputOption="RAW").execute()

    def _format(self, result):
        def stringify(key):
            res = result[key]
            if len(res) == 0:
                return ''
            elif len(res) == 1:
                return res[0]
            else:
                return ', '.join(res)

        return [
                 [ stringify(key) for key in ['name','url','title','email','twitter','linkedin'] ]
               ]

    def add(self, url):
        b = BlogFetch(url, 6)
        res = b.fetch()
        result = self._format(res)
        self._append(values=result, range='')
        return result

    def send(self):
        to_send = self._fetch(range='')
        for row in to_send:
            if not row.is_sent() and row.is_approved():
                if self._email(row):
                    row.set_sent(self)
                    print(row)

    def _email(self, row):
        if all([field != '' for field in row.row[:3]]):
            send_email(row)
            return True
        return False
