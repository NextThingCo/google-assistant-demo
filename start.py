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
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from pydispatch import dispatcher
import subprocess
import threading
import json
import signal
import time
import sys
import os

class GoogleAssistantDemo():
	def __init__(self):
		signal.signal(signal.SIGINT, self.signal_handler)
		
		self.bLostNetworkConnect = False
		
		from statusAudioPlayer import StatusAudioPlayer
		self.statusAudioPlayer = StatusAudioPlayer()
		self.statusAudioPlayer.playWait()
		self.statusAudioPlayer.playThinking(delay=2)

		print ("Starting web werver...")
		from localWebServer import WebServer                           
		self.webServer = WebServer()

		print ("Starting WIFI manager...")
		from wifiConnmanManager import WifiManager
		self.wifiManager = WifiManager() # Manage and evaluate status of wifi/internet connections.
	
		print ("Starting Google applications...")
		from assistantManager import GoogleAssistant
		self.googleAssistant = GoogleAssistant()

		self.setDispatchEvents() # Register functions for any dispatched events.
		self.onWifiConnectionStatus() # Evaluate our wifi and internet connections.
		self.googleAssistant.checkCredentials() # See if Google Assistant's credentials are in place.

		while True:
			time.sleep(0.5)

	# Function to load Google Assistant once the system is ready.
	# This is called from a dispatched event once Google's authentication has been validated.
	def startGoogleAssistant(self):
		if not self.googleAssistant.isRunning():
			self.statusAudioPlayer.playIntro()

		self.googleAssistant.startAssistant()

	# ---------------------------------------------------- #
	#         GOOGLE ASSISTANT SYSTEM EVENTS               #
	# ---------------------------------------------------- #

	# A handler for dispatched events from our implementation of Google Assistant.
	# Passes in a name that indicates what kind of event occured.
	def onGoogleAssistantEvent(self,eventName):
		self.webServer.broadcast('google_assistant_event',eventName)
		if eventName == 'ON_START_FINISHED':
			print 'GoogleAssistant: Ready! Say "Hey Google" or "OK Google" and a question.'
			self.statusAudioPlayer.playReadyAudio()
		if eventName == 'ON_CONVERSATION_TURN_STARTED':
			self.statusAudioPlayer.playListeningAudio()
			print "GoogleAssistant: Waiting for user to finish speaking..."
		if eventName == 'ON_END_OF_UTTERANCE':
			print "GoogleAssistant: User has finished speaking."
		if eventName == 'ON_RESPONDING_FINISHED':
			print "GoogleAssistant: Finished reponse."
		if eventName == 'ON_CONVERSATION_TURN_TIMEOUT':
			self.statusAudioPlayer.playFailureAudio()
			print "GoogleAssistant: Stopped waiting for reply."
		if eventName == 'ON_NO_RESPONSE':
			self.statusAudioPlayer.playFailureAudio()
			print "GoogleAssistant: No valid response to user's sentence."

	# A handler for data coming from our implementation of Google Assistant.
	# The argument will be a JSON object that contains things like the user's parsed speech
	def onGoogleAssistantData(self,data):
		if "text" in data:
			print "GoogleAssistant: User request: \"" + data["text"] + "\""
		elif "with_follow_on_turn" in data and data['with_follow_on_turn']:
			print "GoogleAssistant: Asking follow-up question..."
		elif "is_muted" in data and data['is_muted']:
			print "GoogleAssistant: Muted!"

	# ---------------------------------------------------- #
	#              NETWORK SYSTEM EVENTS                   #
	# ---------------------------------------------------- #

	# Handler for a dispactched event when a user has connected to the device's web interface.
	# If using a USB connection, this address will most likely be http://192.168.82.1/
	def onHTMLConnection(self):
		self.statusAudioPlayer.setUserConnectionStatus(True)
		wifiStatus = self.wifiManager.getStatus()
		self.onWifiConnectionStatus(wifiStatus)
		self.wifiManager.listServices()

		if wifiStatus == 'online' or wifiStatus == 'connecting':
				googleAuthStatus = self.googleAssistant.getAuthorizationStatus()
				self.webServer.broadcast('auth_status',googleAuthStatus)
				if self.googleAssistant.getAuthroizationLink() and googleAuthStatus != "authorized":
						self.webServer.broadcast('google_show_authentication_uri',self.googleAssistant.getAuthroizationLink())

		self.webServer.broadcast('google_assistant_event',self.googleAssistant.getPreviousEvent())
		
	# Handler for a dispatched event when wifi has finished scanning from the WifiManger object.
	def onWifiScan(self,data):
		self.webServer.broadcast('wifi_scan_complete',data) # Tell web frontend to show the available wifi networks
		
	# Handler for dispatch event when the user requests to connect a network from the HTML frontend.
	def onWifiRequestConnection(self,data):
		print "Wifi attempting connection to " + data['ssid']
		self.wifiManager.connect(data['ssid'],data['passphrase'])

	# Event from Wifi Manager object when user has either successfully or unsuccessfully connected to a wifi network.
	def onWifiConnectionStatus(self,statusID=None,msg=None):
		self.getAntennaStatus()

		if not statusID:
			statusID = self.wifiManager.getStatus()

		self.webServer.broadcast('wifi_connection_status',statusID)
		if statusID != "online" and self.googleAssistant.isRunning():
			if not self.bLostNetworkConnect:
				self.statusAudioPlayer.playDisconnected()
				self.statusAudioPlayer.playThinking(delay=6)

			self.bLostNetworkConnect = True
			self.googleAssistant.killAssistant()
			
		elif statusID == "online":
			self.bLostNetworkConnect = False
			self.googleAssistant.checkCredentials()
			self.webServer.broadcast('auth_status',self.googleAssistant.getAuthorizationStatus())
			
	# ---------------------------------------------------- #
	#        GOOGLE AUTHENTICATION SYSTEM EVENTS           #
	# ---------------------------------------------------- #

	# Event for the status of the user's authentication to Google Assistant.
	def onGoogleAuthStatus(self,status):
		if status == 'authorized':
			self.webServer.broadcast('google_authorized',None)
			self.startGoogleAssistant()
		elif status == 'authentication_required':
			self.webServer.broadcast('google_authentication_required',None)
			self.statusAudioPlayer.playSetupInstructions()
		elif status == 'authentication_uri_created':
			self.webServer.broadcast('google_show_authentication_uri',self.googleAssistant.getAuthroizationLink())
		elif status == 'authentication_invalid':
			self.webServer.broadcast('google_authorization_invalid',None)
		elif status == 'no_connection':
			self.webServer.broadcast('google_no_connection',None)
			self.statusAudioPlayer.playSetupInstructions()

	# When the user uploads their client.json file to the web frontend...
	# Get the authorization URL and send it to the web server to display in HTML.
	def onGoogleClientJSONReceived(self,data):
		print "GoogleAssistant: Client JSON received."
		self.googleAssistant.saveClientJSON(data)
		self.googleAssistant.getAuthroizationLink(True)

	# Event for when the user has entered an authentication code from the web interface.
	def onGoogleAuthCodeReceived(self,code):
		self.googleAssistant.setAuthorizationCode(code.strip())
		self.googleAssistant.checkCredentials()

	def onGoogleCredentialsRemove(self,data=None):
		self.googleAssistant.resetCredentials()
	
    # --------------------- #
	#         MISC          #
	# --------------------- #

	# Attach our functions to any dispact signals we care about.
	def setDispatchEvents(self):
		dispatcher.connect( self.onGoogleAssistantEvent,  signal="google_assistant_event", sender=dispatcher.Any )
		dispatcher.connect( self.onGoogleAssistantData, signal="google_assistant_data", sender=dispatcher.Any )
		dispatcher.connect( self.onHTMLConnection, signal="on_html_connection", sender=dispatcher.Any )
		dispatcher.connect( self.onWifiScan, signal="wifi_scan_complete", sender=dispatcher.Any )
		dispatcher.connect( self.onWifiRequestConnection, signal="wifi_user_request_connection", sender=dispatcher.Any )
		dispatcher.connect( self.onWifiConnectionStatus, signal="wifi_connection_status", sender=dispatcher.Any )
		dispatcher.connect( self.setAntennaStatus, signal="wifi_antenna_set", sender=dispatcher.Any )
		dispatcher.connect( self.onGoogleAuthStatus, signal="google_auth_status", sender=dispatcher.Any )
		dispatcher.connect( self.onGoogleClientJSONReceived, signal="google_auth_client_json_received", sender=dispatcher.Any )
		dispatcher.connect( self.onGoogleAuthCodeReceived, signal="google_auth_code_received", sender=dispatcher.Any )
		dispatcher.connect( self.onGoogleCredentialsRemove, signal="google_auth_clear", sender=dispatcher.Any )

	def setAntennaStatus(self,status):
		os.environ['EXT_ANTENNA'] = str(status)
		if not os.path.isdir("/sys/class/gpio/gpio49"):
			os.system("echo 49 > /sys/class/gpio/export")

		os.system("echo 'out' > /sys/class/gpio/gpio49/direction")
		os.system("echo " + str(status) + " > /sys/class/gpio/gpio49/value")
		self.webServer.broadcast('wifi_antenna_status',status)

	def getAntennaStatus(self):
		status = int(os.environ.get('EXT_ANTENNA'))
		self.webServer.broadcast('wifi_antenna_status',status)
		return 
		
	def signal_handler(self, signal, frame):
		self.webServer.shutdown()
		sys.exit(0)

if __name__ == "__main__":
	GoogleAssistantDemo()
