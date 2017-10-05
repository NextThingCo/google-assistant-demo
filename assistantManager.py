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
import pexpect
import psutil
import json
import time
import ast
import os
import string

CLIENT      = '/opt/.config/client.json'
CREDENTIALS = '/opt/.config/credentials.json'

class GoogleAssistant:    
    def __init__(self):
        if not os.path.exists('/opt/.config'):
            os.makedirs('/opt/.config')

        self.flow = None
        self.bNeedAuthorization = True
        self.process = None
        self.authStatus = None
        self.authLink = None
        self.previousEvent = None
        self.killAssistant()

    def startAssistant(self):
        if self.bNeedAuthorization == True and self.checkCredentials() == False:
            return

        if self.isRunning():
            return

        ulimit = 65536
        os.system('ulimit -n ' + str(ulimit))
        dispatcher.send(signal='google_assistant_event',eventName='ON_LOADING')
        self.previousEvent = 'ON_LOADING'
        self.process = pexpect.spawn('google-assistant-demo --credentials ' + CREDENTIALS,timeout=None)

        while self.process.isalive():
            try:
                self.process.expect('\n')
                #print self.process.before.rstrip()
                if self.process.before:
                    self.evalResponse(self.process.before)

            except pexpect.EOF:
                break

    def killAssistant(self):
        if self.process:
            self.process.terminate(True)
            self.process = None

        for proc in psutil.process_iter():
            if proc.name() == 'google-assistan':
                proc.kill()

        dispatcher.send(signal='google_assistant_event',eventName="NOT_RUNNING")

    def isRunning(self):
        try:
            if self.process:
                return True
        except:
            pass

        return False

    def evalResponse(self,output):
        output = ''.join(filter(lambda x: x in string.printable, output)).strip()
        try:
            output = ast.literal_eval(output)
            dispatcher.send(signal='google_assistant_data',data=output)
        except:
            if output.find('ON_') > -1:
                output = output.replace(":","")
                dispatcher.send(signal='google_assistant_event',eventName=output)
                self.previousEvent = output
            elif output.find('timed out'):
                dispatcher.send(signal='google_assistant_event',eventName='TIMEOUT')
                self.previousEvent = 'TIMEOUT'
            elif output.find('is_fatal'):
                pass
            else:
                print("GoogleAssistant: Error processing response: " + output)

    def getPreviousEvent(self):
        return self.previousEvent

    def checkCredentials(self):
        # If Google Assistant is running, assume we are fully authorized.
        if self.isRunning() and os.path.isfile(CREDENTIALS):
            self.setAuthorizationStatus('authorized')
            return True

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
            print("GoogleAssistant: Existing valid token found!")
            return True
        except Exception as e:
            if str(e).find('Failed to establish a new connection') > -1:
                print("GoogleAssistant: Can't connect to server. No internet connection?")
            elif str(e).find('simultaneous read') > -1:
                # A warning from socketio about simultaneous reads.
                # TODO... figure out a better way to handle this. For now, ignore it.
                return
            else:
                print("GoogleAssistant: Authorization error: " + str(e))

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
            print(e)
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
            self.killAssistant()
            self.setAuthorizationStatus('authentication_invalid')
            
            return False

    def resetCredentials(self):

        os.system("rm " + CLIENT)
        os.system("rm " + CREDENTIALS)
        os.system("ls /opt/.config")

        self.authLink = None
        self.killAssistant()
        time.sleep(0.5)
        self.checkCredentials()
        print("Credentials cleared")

