from assistantWrapper import GoogleAssistant
from localWebServer import WebServer
from wifiManager import WifiManager
from pydispatch import dispatcher
import subprocess
import json
import signal
import time
import sys
import os

CLIENT_JSON_FILEPATH = "/opt"

ASSISTANT_LISTENING_AUDIO = "resources/chime_16bit_48k.wav"
ASSISTANT_FAILURE_AUDIO = "resources/unsuccessful_16bit_48k.wav"

INSTRUCTIONS_AUDIO = "resources/instructions.wav"
SETUP_AUDIO = "resources/setup.wav"
INTERNET_RECONNECTED = "resources/internet_reconnected.wav"
INTERNET_DISCONNECTED = "resources/internet_disconnected.wav"

class GoogleAssistantDemo():
	def __init__(self):
		self.wifiManager = WifiManager()
		self.webServer = WebServer()
		self.googleAssistant = GoogleAssistant(CLIENT_JSON_FILEPATH)
		self.bLostConnection = False
		self.bPlayedSetupInstructions = False
		self.googleAuthStatus = None
		self.setDispatchEvents()
		self.onWifiConnectionStatus(self.wifiManager.getStatus())
		signal.signal(signal.SIGINT, self.signal_handler)

		self.googleAssistant.checkCredentials()

		while True:
			time.sleep(0.5)

				
	# A handler for dispatched events from our implementation of Google Assistant.
	# Passes in a name that indicates what kind of event occured.
	def onGoogleAssistantEvent(self,eventName):
		if eventName == 'ON_START_FINISHED':
			print "GoogleAssistant: Ready! Say \"Hey Google\" or \"OK Google\" and a question."
		if eventName == 'ON_CONVERSATION_TURN_STARTED':
			self.playAudio(ASSISTANT_LISTENING_AUDIO,False)
			print "GoogleAssistant: Waiting for user to finish speaking..."
		if eventName == 'ON_END_OF_UTTERANCE':
			print "GoogleAssistant: User has finished speaking."
		if eventName == 'ON_RESPONDING_FINISHED':
			print "GoogleAssistant: Finished reponse."
		if eventName == 'ON_CONVERSATION_TURN_TIMEOUT':
			self.playAudio(ASSISTANT_FAILURE_AUDIO,False)
			print "GoogleAssistant: Stopped waiting for reply."
		if eventName == 'ON_NO_RESPONSE':
			self.playAudio(ASSISTANT_FAILURE_AUDIO,False)
			print "GoogleAssistant: No valid response to user's sentence."

	# A handler for data coming from our implementation of Google Assistant.
	# The argument will be a JSON object that contains things like the user's parsed speech...
	# ... and if Google Assistant is asking a follow up question.
	def onGoogleAssistantData(self,data):
		if "text" in data:
			print "GoogleAssistant: User request: \"" + data["text"] + "\""
		elif "with_follow_on_turn" in data:
			if data['with_follow_on_turn'] == True:
				print "GoogleAssistant: Asking follow-up question..."
		elif "is_muted" in data:
			if data['is_muted'] == True:
				print "GoogleAssistant: Muted!"

	# Handler for a dispactched event when a user has connected to the device's web interface.
	# If using a USB connection, this address will be http://192.168.82.1/
	def onHTMLConnection(self):
		self.wifiManager.listServices()
		self.googleAssistant.checkCredentials()
		self.googleAssistant.getAuthorizationStatus()
		self.webServer.emit('wifi_connection_status',self.wifiManager.getStatus())
		
	# Handler for a dispatched event when wifi has finished scanning from the WifiManger object.
	def onWifiScan(self,data):
		print "Wifi scan complete."
		self.webServer.emit('wifi_scan_complete',data) # Tell web frontend to show the available wifi networks
		
	# Handler for dispatch event from web socket when user requests to connect a network from the HTML frontend.
	def onWifiRequestConnection(self,data):
		print "Wifi attempting connection to " + data['ssid']
		print data
		print data['passphrase']
		self.wifiManager.connect(data['ssid'],data['passphrase'])

	# Event from Wifi Manager object when user has either successfully or unsuccessfully connected to a wifi network.
	def onWifiConnectionStatus(self,statusID):
		self.webServer.emit('wifi_connection_status',statusID)
		if statusID != "online" and self.googleAssistant.isRunning():
			self.bLostConnection = True
			self.googleAssistant.killAssistant()
			self.playAudio(INTERNET_DISCONNECTED,True)
		elif statusID == "online":
			self.googleAssistant.checkCredentials()

	# Event for the status of the user's authentication to Google Assistant.
	def onGoogleAuthStatus(self,status):
		print ("AUTH STATUS!")
		self.googleAuthStatus = status

		self.webServer.emit('auth_status',status)
		print status
		if status == 'authentication_required':
			self.webServer.emit('google_authentication_required',None)
			if not self.bPlayedSetupInstructions:
				self.bPlayedSetupInstructions = True
				self.playAudio(SETUP_AUDIO,False)

		elif status == 'authentication_uri_created':
			self.webServer.emit('google_show_authentication_uri',self.googleAssistant.getAuthroizationLink())
		elif status == 'authentication_invalid':
			self.webServer.emit('google_authorization_invalid',None)
		elif status == 'authorized':
			self.webServer.emit('google_authorized',None)
			self.playAudio(INSTRUCTIONS_AUDIO,False)
			self.googleAssistant.startAssistant()
		elif status == 'no_connection':
			self.webServer.emit('google_no_connection',None)

	# When the user uploads their client.json file to the web frontend...
	# Get the authorization URL and send it to the web server to display in HTML.
	def onGoogleClientJSONReceived(self,data):
		file = CLIENT_JSON_FILEPATH+"/client.json"
		if os.path.exists(file):
			os.remove(file)

		with open(file, 'w') as outfile:
			json.dump(data, outfile)

		print "GoogleAssistant: Client JSON received."
		print self.googleAssistant.getAuthroizationLink()
		self.webServer.emit('google_show_authentication_uri',self.googleAssistant.getAuthroizationLink())

	# Event for when the user has entered an authentication code from the web interface.
	def onGoogleAuthCodeReceived(self,code):
		print (" SETTING AUTH CODE?")
		#code = data['code']
		#print data['code']
		print code
		# Send the authorization code to Google to complete the setup.
		self.googleAssistant.setAuthorizationCode(code.strip())
		self.googleAssistant.checkCredentials()

	# Attach our functions to any dispact signals we care about.
	def setDispatchEvents(self):
		dispatcher.connect( self.onGoogleAssistantEvent.__get__(self, GoogleAssistantDemo),  signal="google_assistant_event", sender=dispatcher.Any )
		dispatcher.connect( self.onGoogleAssistantData.__get__(self, GoogleAssistantDemo), signal="google_assistant_data", sender=dispatcher.Any )
		dispatcher.connect( self.onHTMLConnection.__get__(self, WifiManager), signal="on_html_connection", sender=dispatcher.Any )
		dispatcher.connect( self.onWifiScan.__get__(self, WifiManager), signal="wifi_scan_complete", sender=dispatcher.Any )
		dispatcher.connect( self.onWifiRequestConnection.__get__(self, GoogleAssistantDemo), signal="wifi_user_request_connection", sender=dispatcher.Any )
		dispatcher.connect( self.onWifiConnectionStatus.__get__(self, GoogleAssistantDemo), signal="wifi_connection_status", sender=dispatcher.Any )
		dispatcher.connect( self.onGoogleAuthStatus.__get__(self, GoogleAssistantDemo), signal="google_auth_status", sender=dispatcher.Any )
		dispatcher.connect( self.onGoogleClientJSONReceived.__get__(self, GoogleAssistantDemo), signal="google_auth_client_json_received", sender=dispatcher.Any )
		dispatcher.connect( self.onGoogleAuthCodeReceived.__get__(self, GoogleAssistantDemo), signal="google_auth_code_received", sender=dispatcher.Any )

	def playAudio(self,audioFile,bBlocking):
		FNULL = open(os.devnull, 'w')
		self.audioProcess = subprocess.Popen(['aplay', audioFile],stdout=FNULL,stderr=subprocess.STDOUT)

	def signal_handler(self, signal, frame):
		self.webServer.shutdown()
		sys.exit(0)

if __name__ == "__main__":
	GoogleAssistantDemo()