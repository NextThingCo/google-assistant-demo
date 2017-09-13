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

CREDENTIALS = '/opt/credentials.json'

class GoogleAssistant:    
    def __init__(self,clientJSONPath):
        self.clientJSONPath = clientJSONPath
        self.flow = None
        self.bNeedAuthorization = True
        self.process = None
        self.authStatus = None
        self.authLink = None
        self.killAssistant()

    def startAssistant(self):
        self.killAssistant() # Kill any Assistant processes that may already be running.
        if self.bNeedAuthorization == True and self.checkCredentials() == False:
            return

        ulimit = 65536
        os.system('ulimit -n ' + str(ulimit))
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
            elif output.find('timed out'):
                dispatcher.send(signal='google_assistant_event',eventName='TIMEOUT')
            elif output.find('is_fatal'):
                pass
            else:
                print "GoogleAssistant: Error processing response: " + output

    def checkCredentials(self):
        # Check for existing (and valid) credentials.
        clientFile = self.clientJSONPath+'/client.json'

        if not os.path.isfile(CREDENTIALS) or not os.path.isfile(clientFile):
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
            print "GoogleAssistant: Existing valid token found!"
            self.bNeedAuthorization = False
            self.setAuthorizationStatus('authorized')
            return True
        except Exception as e:
            if str(e).find('Failed to establish a new connection') > -1:
                print "GoogleAssistant: Can't connect to server. No internet connection?"
            else:
                print "GoogleAssistant: Authorization error: " + str(e)

            self.setAuthorizationStatus('no_connection')
            self.bNeedAuthorization = True
        return False

    def setAuthorizationStatus(self,status):
        if status != self.authStatus or status == 'authorized':
            dispatcher.send(signal='google_auth_status',status=status)

        self.authStatus = status

    def getAuthorizationStatus(self):
        return self.authStatus

    def getAuthroizationLink(self,bRefresh=False):
        if self.authLink != None and not bRefresh:
            return self.authLink

        data = None
        with open(self.clientJSONPath+'/client.json') as data_file:    
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

            if os.path.isfile(CREDENTIALS):
                os.remove(CREDENTIALS)

            self.authLink = self.flow.step1_get_authorize_url()
            self.setAuthorizationStatus('authentication_uri_created')
            return self.authLink
        except Exception as e:
            print e
            return False

    def setAuthorizationCode(self,authCode):
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