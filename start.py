from assistantWrapper import GoogleAssistant
from localWebServer import WebServer
from wifiManager import WifiManager
from pydispatch import dispatcher
import subprocess
import signal
import sys

ASSISTANT_LISTENING_AUDIO = "resources/chime_16bit_48k.wav"
ASSISTANT_FAILURE_AUDIO = "resources/unsuccessful_16bit_48k.wav"

class GoogleAssistantDemo():
	def __init__(self):
		self.wifiManager = WifiManager()
		self.webServer = WebServer()
		self.googleAssistant = GoogleAssistant('/opt')
		self.setDispatchEvents()
		self.onWifiConnectionStatus(self.wifiManager.getStatus())
		signal.signal(signal.SIGINT, self.signal_handler)

		# If we are connected to the internet, start Google Assistant! Otherwise, wait until we are.
		while True:
			if self.wifiManager.getStatus() == "online" and not self.googleAssistant.isRunning():
				self.googleAssistant.startAssistant()
				
	# A handler for dispatched events from our implementation of Google Assistant.
	# Passes in a name that indicates what kind of event occured.
	def onGoogleAssistantEvent(self,eventName):
		if eventName == 'ON_START_FINISHED':
			print "GoogleAssistant: Ready! Say \"Hey Google\" or \"OK Google\" and a question."
		if eventName == 'ON_CONVERSATION_TURN_STARTED':
			self.playAudio(ASSISTANT_LISTENING_AUDIO)
			print "GoogleAssistant: Waiting for user to finish speaking..."
		if eventName == 'ON_END_OF_UTTERANCE':
			print "GoogleAssistant: User has finished speaking."
		if eventName == 'ON_RESPONDING_FINISHED':
			print "GoogleAssistant: Finished reponse."
		if eventName == 'ON_CONVERSATION_TURN_TIMEOUT':
			self.playAudio(ASSISTANT_FAILURE_AUDIO)
			print "GoogleAssistant: Stopped waiting for reply."
		if eventName == 'ON_NO_RESPONSE':
			self.playAudio(ASSISTANT_FAILURE_AUDIO)
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
		self.webServer.emit('wifi_connection_status',self.wifiManager.getStatus())
		self.wifiManager.listServices()

	# Handler for a dispatched event when wifi has finished scanning from the WifiManger object.
	def onWifiScan(self,data):
		print "Wifi scan complete."
		self.webServer.emit('wifi_scan_complete',data) # Tell web frontend to show the available wifi networks
		# TODO... remove this
		self.wifiManager.connect("NTC 2461","ntc2461@ccess")
		
	# Handler for dispatch event from web socket when user requests to connect a network from the HTML frontend.
	def onWifiRequestConnection(self,data):
		print "Wifi attempting connection to " + data['ssid']
		self.wifiManager.connect(data['ssid'],data['passphrase'])

	# Event from Wifi Manager object when user has either successfully or unsuccessfully connected to a wifi network.
	def onWifiConnectionStatus(self,statusID):
		if statusID != "online" and self.googleAssistant.isRunning():
			self.playAudio(ASSISTANT_FAILURE_AUDIO)
			self.googleAssistant.killAssistant()

		self.webServer.emit('wifi_connection_status',statusID)

	# Event for the status of the user's authentication to Google Assistant.
	def onGoogleAuthStatus(self,statusCode,msg):
		print "STATUS " + str(statusCode)
		if statusCode == 0:
			self.webServer.emit('google_authentication_required',msg)
		elif statusCode == 1:
			self.webServer.emit('google_show_authentication_uri',msg)
		elif statusCode == 2:
			self.webServer.emit('google_authorization_invalid',msg)
		elif statusCode == 3:
			self.webServer.emit('google_authorized',msg)
		elif statusCode == 4:
			self.webServer.emit('google_no_connection',msg)

	# Event for when the user has entered an authentication code from the web interface.
	def onGoogleAuthCodeReceived(self,authCode):
		# Send the authorization code to Google to complete the setup.
		self.googleAssistant.setAuthorizationCode(authCode)

	# Attach our functions to any dispact signals we care about.
	def setDispatchEvents(self):
		dispatcher.connect( self.onGoogleAssistantEvent.__get__(self, GoogleAssistantDemo),  signal="google_assistant_event", sender=dispatcher.Any )
		dispatcher.connect( self.onGoogleAssistantData.__get__(self, GoogleAssistantDemo), signal="google_assistant_data", sender=dispatcher.Any )
		dispatcher.connect( self.onHTMLConnection.__get__(self, WifiManager), signal="on_html_connection", sender=dispatcher.Any )
		dispatcher.connect( self.onWifiScan.__get__(self, WifiManager), signal="wifi_scan_complete", sender=dispatcher.Any )
		dispatcher.connect( self.onWifiRequestConnection.__get__(self, GoogleAssistantDemo), signal="wifi_user_request_connection", sender=dispatcher.Any )
		dispatcher.connect( self.onWifiConnectionStatus.__get__(self, GoogleAssistantDemo), signal="wifi_connection_status", sender=dispatcher.Any )
		dispatcher.connect( self.onGoogleAuthStatus.__get__(self, GoogleAssistantDemo), signal="google_auth_status", sender=dispatcher.Any )
		dispatcher.connect( self.onGoogleAuthCodeReceived.__get__(self, GoogleAssistantDemo), signal="google_auth_code_received", sender=dispatcher.Any )

	def playAudio(self,audioFile):
		proc = subprocess.Popen(['aplay', audioFile],stdout=subprocess.PIPE)

	def signal_handler(self, signal, frame):
		sys.exit(0)

if __name__ == "__main__":
	GoogleAssistantDemo()