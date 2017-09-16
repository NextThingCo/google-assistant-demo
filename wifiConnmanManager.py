import dbus.mainloop.glib
import subprocess
import threading
import pyconnman
import gobject
import urllib2
import dbus
import time
import sys
import os

from pydispatch import dispatcher

STATUS_DISCONNECTED		= "disconnected" 	# Not connected to any wifi network
STATUS_REJECTION		= "rejected"		# Connection attempt was refused. Possibly bad password.
STATUS_OFFLINE			= "offline"			# Connected to wifi network with no internet connection
STATUS_ONLINE			= "online"			# Connected to wifi network with valid internet connection
STATUS_CONNECTING		= "connecting"		# Attempting to connect to a network

NETWORK_TIMEOUT			= 2					# Number of seconds to give up on trying to the internet

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
gobject.threads_init()

class WifiManager():
	def __init__(self):
		self.manager = pyconnman.ConnManager()
		self.status = STATUS_DISCONNECTED
		self.agent = None
		self.services = None

		self.waitForWifiInterface()
		self.setWifiPower(True)
		self.listServices()

		# Monitor the state of wifi and internet status every few seconds.
		def monitor():
			while True:
				self.getStatus()
				time.sleep(3)

		t = threading.Thread(target=monitor, args = ())
		t.setDaemon(True)
		t.start()

	# Wait until the WiFi interface exists and is ready to be used.
	def waitForWifiInterface(self):
		technologies = self.manager.get_technologies()
		while True:
			for i in technologies:
 				(path, params) = i
				if params['Name'] == 'WiFi':
					return
				
			time.sleep(1)

	def getStatus(self):
		status = None
		state = self.manager.get_property(name='State')
		# See if we're logged into an access point.
		if state == "online":
			# Ping Google to see if we have an internet connection.
			try:
				urllib2.urlopen('http://216.58.192.142', timeout=NETWORK_TIMEOUT)
				status = STATUS_ONLINE
			except:
				status = STATUS_OFFLINE

		# If not connected to any wifi network...
		elif state == "idle":
			status = STATUS_DISCONNECTED
			self.reconnect()
	
		return self.setStatus(status)

	def setStatus(self,status):
		if self.status != status:
			def dispatchEvent():
				try:
					dispatcher.send(signal="wifi_connection_status",statusID=status)
				except:
					pass

			# Start dispatcher in a new thread in case the listener is blocking us.
			t = threading.Thread(target=dispatchEvent, args = ())
			t.start()
		
		self.status = status
		return self.status

	# Do a hard reset of the wifi interface.
	def reset(self):
		self.setWifiPower(False)
		FNULL = open(os.devnull, 'w')
		subprocess.call(['rfkill','block','1'],stdout=FNULL)
		subprocess.call(['rfkill','unblock','1'],stdout=FNULL)
		self.setWifiPower(True)
		self.waitForWifiInterface()
		self.listServices()

	# Check if an agent has already been set up for an access point with the specified path.
	def agentExists(self,path):
		agents = os.listdir('/var/lib/connman')
		for agent in agents:
			if path == '/net/connman/service/' + agent:
				return True

		return False

	# Attempt to reconnect to a previous wifi agent
	def reconnect(self):
		if self.services == None:
			self.listServices()
			return

		for (path, params) in self.services:
			if self.agentExists(path):
				print ("Attempting to reconnect to " + params['Name'])
				dispatcher.send(signal="wifi_connection_status",statusID=STATUS_CONNECTING)
				try:
					service = pyconnman.ConnService(path)
					service.connect()
					return True
				except dbus.exceptions.DBusException:
					exception = str(dbus.String(sys.exc_info()[1]))
					if exception.find('AlreadyConnected') != -1:
						dispatcher.send(signal="wifi_connection_status",statusID=STATUS_ONLINE)
						print("Already connected!")
					elif exception.find('Input/output error') != -1:
						print "Connman I/O error! Attempting to reset."
						dispatcher.send(signal="wifi_connection_status",statusID=STATUS_DISCONNECTED)
						self.reset()
					else:
						dispatcher.send(signal="wifi_connection_status",statusID=STATUS_DISCONNECTED)
						print "WIFI ERROR!"
						print exception
						self.reset()

		return False

	def setWifiPower(self,bState):
		tech = pyconnman.ConnTechnology('/net/connman/technology/wifi')
		if tech.get_property('Powered') == 0 and bState == True:
			tech.set_property('Powered', 1)
			print tech.get_property('Powered')
		elif tech.get_property('Powered') == 1 and bState == False:
			tech.set_property('Powered', 0)
			print tech.get_property('Powered')

	# Return a list of available wifi networks. The list contains an entry for each path.
	# Each path entry has three attributes: ssid (wifi network name), security (psk, none, etc), and strength.
	def listServices(self):
		def list():
			tech = pyconnman.ConnTechnology('/net/connman/technology/wifi')
			tech.scan()
			self.services = self.manager.get_services()
			wifiList = {}
			for (path, params) in self.services:
				try:
					wifiList[path] = {}
					wifiList[path]['ssid'] = str(dbus.String(params['Name']))
					wifiList[path]['security'] = str(dbus.String(params['Security'][0]))
					wifiList[path]['strength'] = int(dbus.Byte(params['Strength']))
				except:
					pass

			dispatcher.send(signal="wifi_scan_complete",data=wifiList)

		t = threading.Thread(target=list, args = ())
		t.setDaemon(True)
		t.start()

	def connect(self,ssid=None,passphrase=None,name=None,identity=None,username=None,password=None,wpspin=None):
		if self.services == None:
			self.listServices()

		servicePath = None
		for (path, params) in self.services:
			try:
				if str(dbus.String(params['Name'])) == ssid:
					servicePath = path
			except:
				pass

		if not servicePath:
			print("No wifi network found")
			return

		print "Attempting to connect to " + ssid + "..."
		dispatcher.send(signal="wifi_connection_status",statusID=STATUS_CONNECTING)
		try:
			self.agent = pyconnman.SimpleWifiAgent('/test/agent')
			self.agent.set_service_params(servicePath,name,ssid,identity,username,password,passphrase,wpspin)
			self.manager.register_agent('/test/agent')
			service = pyconnman.ConnService(servicePath)
			service.connect()
			dispatcher.send(signal="wifi_connection_status",statusID=STATUS_ONLINE)
		except dbus.exceptions.DBusException:
			exception = str(dbus.String(sys.exc_info()[1]))
			print exception
			if exception.find('AlreadyConnected') != -1:
				dispatcher.send(signal="wifi_connection_status",statusID=STATUS_ONLINE)
				pass
			elif exception.find('NoReply') != -1:
				dispatcher.send(signal="wifi_connection_status",statusID=STATUS_REJECTION)