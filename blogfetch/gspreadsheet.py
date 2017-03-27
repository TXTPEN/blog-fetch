from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

from blogfetch import BlogFetch

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

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

    def _fetch(self, range='A1:G2'):
        if range != '':
            range_name = self.sheet + '!' + range
        else:
            range_name = self.sheet

        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id, range=range_name).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
        else:
            for row in values:
                print(row)

    def _update(self,
               values=[['JT Cho', 'http://blog.jtcho.me/100-prisoners-and-a-lightbulb/', 'jonathan.t.cho@gmail.com', '100 Prisoners and a Lightbulb']],
               range="A3:G3"):
        if range != '':
            range_name = self.sheet + '!' + range
        else:
            range_name = self.sheet
        body = {'values': values}
        result = self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id, range=range_name,
                    body=body, valueInputOption="RAW").execute()

    def _append(self,
               values=[['JT Cho', 'http://blog.jtcho.me/100-prisoners-and-a-lightbulb/', 'jonathan.t.cho@gmail.com', '100 Prisoners and a Lightbulb']],
               range="A3:G3"):
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

    def add(self, url="http://rickyhan.com"):
        b = BlogFetch(url, 10)
        res = b.fetch()
        result = self._format(res)
        self._append(values=result, range='')
