from __future__ import print_function

import os.path
import base64
import re # regex
import unicodedata
from bs4 import BeautifulSoup

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

#constants
max_emails = 10 # Get the last 3 e-mails. We assume that H-Q would never send more than 3 e-mails at once.
sender_query = "from:hydroquebec@communication.hydroquebec.com" # Query only the e-mails from H-Q.

def main():
    """Long comment
    Long comment
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API ("Create a service")
        service = build('gmail', 'v1', credentials=creds)

        #message_results is a thing that contains:
        #1. A message list. Each message ressource contains onli an id and a threadId
        #2. A token to retrieve the next page of results in the list
        #3. The estimated number of results
        message_results = service.users().messages().list(maxResults=max_emails,
                                                          q=sender_query,
                                                          userId="me").execute()

        #Then, in message_results, we only keep the message_list
        #(Gets the 'messages' in message_result)
        message_list = message_results.get('messages')

        complete_list = ""

        # for every thing in message_list (a list of message IDs)
        for msg in message_list:
            # Get the message from its id. (The ressource type of "message" is "Message")
            message = service.users().messages().get(userId='me', id=msg['id']).execute()


            # Get the payload from the message (The ressource type of "payload" is "MessagePart")
            payload = message['payload']
            headers = payload['headers']

            # Look for Subject and Sender Email in the headers
            # There are many headers. Each of them has a 'name' and a 'value'
            for d in headers:
                if d['name'] == 'Subject':
                    subject = d['value']
                #if d['name'] == 'From':
                #    sender = d['value']

            subject_regex_result = re.match("Avis.*pointe",subject)
            subject_is_match = bool(subject_regex_result)

            #if subject_is_match:
                #print("Subject is a match")
            #else:
                #print("Subject isn't a match")

            # The Body of the message is encoded in base64url. So, we have to decode it.
            # Get the data and decode it with the base64 module.
            #text = payload.get('body')[0]
            data = payload['body']['data']
            #data = data.replace("-", "+").replace("_", "/")
            decoded_data = base64.urlsafe_b64decode(data)# Gmail uses base64url, not plain base64

            # Now, the data obtained is in lxml. So, we will parse
            # it with the BeautifulSoup library
            soup = BeautifulSoup(decoded_data, "lxml")
            body = soup.body()
            #unordered_lists = soup.find_all('ul') #return all the unordered lists
            unordered_list_text = soup.ul.text #returns the text of the first unordered list

            # Regex pour matcher la date: /^([0-9][0-9]?)\D.*(janvier|février|mars|avril|octobre|novembre|décembre).+?de.+?([0-9][0-9]?).+?à.+?([0-9][0-9]?)/gm

            complete_list += unordered_list_text


            # Printing the subject, sender's email and message
            #print("Subject: ", subject)
            #print("From: ", sender)
            #print("Message: ", body)
            #print("Unordered lists ", unordered_lists)
            #print(unordered_list_text)
            #print('\n')

        complete_list = complete_list.splitlines()
        complete_list = list(filter(None, complete_list))
        #complete_list = unicodedata.normalize("NFC",complete_list)
        print(complete_list)


        for str in complete_list:
            normalized = str.replace(u'\xa0', u' ')
            #normalized = unicodedata.normalize("NFC",str)
            m = re.search(r"^([0-9][0-9]?)\D.*(janvier|février|mars|avril|octobre|novembre|décembre).+?de.+?([0-9][0-9]?).+?à.+?([0-9][0-9]?)",normalized)
            period = {'day': m.group(1), 'month': m.group(2), 'startHour': m.group(3), 'endHour': m.group(4)}
            print(period)

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f'An error occurred: {error}')


if __name__ == '__main__':
    main()
