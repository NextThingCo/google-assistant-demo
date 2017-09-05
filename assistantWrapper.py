from oauth2client.client import OAuth2WebServerFlow
from pydispatch import dispatcher
import google.auth.transport.requests
import google.oauth2.credentials
import pexpect
import psutil
import json
import time
import ast
import os
import string

LOG_DIR = '/opt/assistant.log'
CREDENTIALS = '/root/.config/google-oauthlib-tool/credentials.json'
#CREDENTIALS = '/opt/credentials.json'

class GoogleAssistant:    
    def __init__(self,clientJSONPath):
        self.clientJSONPath = clientJSONPath
        self.flow = None
        self.bNeedAuthorization = True
        self.process = None
        self.killAssistant()

    def startAssistant(self):
        self.killAssistant() # Kill any Assistant processes that may already be running.
        if self.bNeedAuthorization == True and self.checkCredentials() == False:
            return

        ulimit = 65536
        os.system('ulimit -n ' + str(ulimit))
        self.process = pexpect.spawn('google-assistant-demo',timeout=None)

        while self.process.isalive():
            try:
                self.process.expect('\n')
                #print self.process.before.rstrip()
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
            if type(output)=='string':
                if output.find('ON_') > -1:
                    output = output.replace(":","")
                    dispatcher.send(signal='google_assistant_event',eventName=output)
                elif output.find('timed out'):
                    dispatcher.send(signal='google_assistant_event',eventName='TIMEOUT')
                elif output.find('is_fatal'):
                    self.startAssistant()
                else:
                    print "GoogleAssistant: Error processing response: " + output

    def checkCredentials(self):
        # Check for existing (and valid) credentials.
        try:
            credentials = google.oauth2.credentials.Credentials(token=None,**json.load(open(CREDENTIALS)))
            http_request = google.auth.transport.requests.Request()
            credentials.refresh(http_request)
            print "GoogleAssistant: Existing valid token found!"
            self.bNeedAuthorization = False
            dispatcher.send(signal='google_auth_status',statusCode=3,msg="existing valid token")
            self.startAssistant()
            return True
        except Exception as e:
            print e
            dispatcher.send(signal='google_auth_status',statusCode=4,msg=e)
            self.bNeedAuthorization = True
            return False

        clientFile = self.clientJSONPath+'/client.json'
        if not os.path.isfile(clientFile) and self.bNeedAuthorization:
            print "GoogleAssistant: JSON client not found"

        if self.bNeedAuthorization:
            print( "GoogleAssistant: Authentication needed!")
            dispatcher.send(signal='google_auth_status',statusCode=0,msg=None)
            return False
        else:
            clientID = '742105191129-4cgf6lmb6gbmd122g0g5hnac4gs01fdp.apps.googleusercontent.com'
            scope = 'https://www.googleapis.com/auth/assistant-sdk-prototype'
            uri = 'urn:ietf:wg:oauth:2.0:oob'
            self.flow = OAuth2WebServerFlow(client_id=clientID,
                           client_secret='your_client_secret',
                           scope=scope,
                           redirect_uri=uri)

            auth_uri = self.flow.step1_get_authorize_url()
            dispatcher.send(signal='google_auth_status',statusCode=1,msg=auth_uri)
            print auth_uri
            # TODO REMOVE THIS!!!!!!!!!!!!!!!!!!
            self.setAuthorizationCode("garbage")

    def setAuthorizationCode(self,authCode):
        try:
            credentials = self.flow.step2_exchange(authCode)
            dispatcher.send(signal='google_auth_status',statusCode=3,msg=None)
            self.startAssistant()
            self.bNeedAuthorization = False
            return True
        except:
            print( "Authorization failed!")
            self.bNeedAuthorization = True
            dispatcher.send(signal='google_auth_status',statusCode=2,msg=None)
            return False