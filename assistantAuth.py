# Copyright (C) 2017 Next Thing Co. <software@nextthing.co>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License

from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage
from oauth2client import tools
from pydispatch import dispatcher
import google.auth.transport.requests
import google.oauth2.credentials
import httplib2
import json
import os
import string

CLIENT      = '/opt/.config/client.json'
CREDENTIALS = '/opt/.config/credentials.json'

DEFAULT_ULIMIT = 65536

class GoogleAssistantAuthorization:    
    def __init__(self):
        if not os.path.exists('/opt/.config'):
            os.makedirs('/opt/.config')

        os.system('ulimit -n ' + str(DEFAULT_ULIMIT))

        self.flow = None
        self.bNeedAuthorization = True
        self.authStatus = None
        self.authLink = None

    def checkCredentials(self):
        # Check for existing (and valid) credentials.
        if not os.path.isfile(CREDENTIALS) or not os.path.isfile(CLIENT):
            self.bNeedAuthorization = True
            print( "GoogleAssistant: Authentication needed!")
            if not self.authLink:
                self.setAuthorizationStatus('authentication_required')
            return False

        # Both client JSON and credentials files exist. Attempt to authenticate!
        try:
            credentials = google.oauth2.credentials.Credentials(token=None,**json.load(open(CREDENTIALS)))
            http_request = google.auth.transport.requests.Request()
            credentials.refresh(http_request)
            self.authLink = None
            self.bNeedAuthorization = False
            self.setAuthorizationStatus('authorized')
            print "GoogleAssistant: Existing valid token found!"
            return True
        except Exception as e:
            if str(e).find('Failed to establish a new connection') > -1:
                print "GoogleAssistant: Can't connect to server. No internet connection?"
            elif str(e).find('simultaneous read') > -1:
                # A warning from socketio about simultaneous reads.
                # TODO... figure out a better way to handle this. For now, ignore it.
                return
            else:
                print "GoogleAssistant: Authorization error: " + str(e)

            self.setAuthorizationStatus('no_connection')
            self.bNeedAuthorization = True
        return False

    def setAuthorizationStatus(self,status,bForce=False):
        if status != self.authStatus or status == 'authorized' or bForce:
            dispatcher.send(signal='google_auth_status',status=status)

        self.authStatus = status

    def getAuthorizationStatus(self):
        return self.authStatus

    def saveClientJSON(self,data):
        if os.path.exists(CLIENT):
            os.remove(CLIENT)

        if os.path.isfile(CREDENTIALS):
            os.remove(CREDENTIALS)

        with open(CLIENT, 'w') as outfile:
            json.dump(data, outfile)


    def getAuthroizationLink(self,bRefresh=False):
        if not self.getAuthorizationStatus():
            return

        if self.getAuthorizationStatus() == 'authorized' or self.previousEvent == 'ON_LOADING' or os.path.isfile(CREDENTIALS):
            self.authLink = None
            return

        if self.authLink != None and not bRefresh:
            return self.authLink

        if not os.path.isfile(CLIENT):
            return

        data = None
        with open(CLIENT) as data_file:    
            data = json.load(data_file)

        try:
            clientID = data['installed']['client_id']
            clientSecret = data['installed']['client_secret']
            uri = data['installed']['redirect_uris'][0]
            scope = 'https://www.googleapis.com/auth/assistant-sdk-prototype'

            self.flow = OAuth2WebServerFlow(client_id=clientID,
                client_secret=clientSecret,
                scope=scope,
                redirect_uri=uri)

            self.authLink = self.flow.step1_get_authorize_url()
            self.setAuthorizationStatus('authentication_uri_created',True)
            return self.authLink
        except Exception as e:
            print e
            return False

    def setAuthorizationCode(self,authCode):
        self.authLink = None
        try:
            credentials = self.flow.step2_exchange(authCode)
            credentials.authorize(httplib2.Http())
            jsonCredentials = json.loads(credentials.to_json())

            data = {}
            data['scopes'] = ['https://www.googleapis.com/auth/assistant-sdk-prototype']
            data['token_uri'] = jsonCredentials['token_uri']
            data['client_id'] = jsonCredentials['client_id']
            data['client_secret'] = jsonCredentials['client_secret']
            data['refresh_token'] = jsonCredentials['refresh_token']

            with open(CREDENTIALS, 'w') as outfile:
                json.dump(data, outfile)

            return True
        except Exception as e:
            print( "Authorization failed! " + str(e))
            self.bNeedAuthorization = True
            self.setAuthorizationStatus('authentication_invalid')
            
            return False

    def resetCredentials(self):
        try: os.remove(CREDENTIALS)
        except: pass
        
        try: os.remove(CLIENT)
        except: pass

        self.authLink = None

        print "Credentials cleared"

