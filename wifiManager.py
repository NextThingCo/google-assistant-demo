from pydispatch import dispatcher
import pyconnman
import dbus
import dbus.mainloop.glib
import threading
import gobject
import time
import urllib2
import sys
import subprocess
import os

STATUS_DISCONNECTED		= "disconnected" 	# Not connected to any wifi network
STATUS_OFFLINE			= "offline"			# Connected to wifi network with no internet connection
STATUS_ONLINE			= "online"			# Connected to wifi network with valid internet connection

NETWORK_TIMEOUT			= 5					# Number of seconds to give up on trying to the internet

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
gobject.threads_init()

class WifiManager():
	def __init__(self):
		self.manager = pyconnman.ConnManager()
		self.status = STATUS_DISCONNECTED
		self.service = None

		def update():
			while True:
				self.getStatus()
				time.sleep(2)

		t = threading.Thread(target=update, args = ())
		t.setDaemon(True)
		t.start()

		self.setWifiPower(True)
		self.listServices()
		#bWaitingForWifi = True

		#technologies = self.manager.get_technologies()
		#while bWaitingForWifi:
		#	for i in technologies:
 		#		(path, params) = i
		#		print params['Name']
		#		if params['Name'] == 'WiFi':
		#			bWaitingForWifi = False

	def getStatus(self):
		status = STATUS_DISCONNECTED
		if self.manager.get_property(name='State') != "idle":
			try:
				urllib2.urlopen('http://216.58.192.142', timeout=NETWORK_TIMEOUT)
				return self.setStatus(STATUS_ONLINE)
			except:
				print( "No internet connection found!")
				status = STATUS_OFFLINE
				pass
		else:
			try:
				self.reconnect()
			except:
				pass

		return self.setStatus(status)

	def setStatus(self,status):
		self.status = status
		dispatcher.send(signal="wifi_connection_status",statusID=self.status)
		return self.status

	# Check if an agent has already been set up for an access point with the specified path.
	def agentExists(self,path):
		agents = os.listdir('/var/lib/connman')
		for agent in agents:
			if path == '/net/connman/service/'+agent:
				return True

		return False

	def reset(self):
		self.setWifiPower(False)
		subprocess.call(['rfkill','block','1'],stdout=FNULL)
		subprocess.call(['rfkill','unblock','1'],stdout=FNULL)
		self.setWifiPower(True)
		self.listServices()

	# Attempt to reconnect to a previous wifi agent
	def reconnect(self):
		for (path, params) in self.services:
			if self.agentExists(path) and params['AutoConnect'] == True:
				print ("Attempting to reconnect to " + params['Name'])
				try:
					service = pyconnman.ConnService(path)
					service.connect()
					break
				except dbus.exceptions.DBusException:
					exception = str(dbus.String(sys.exc_info()[1]))
					if exception.find('AlreadyConnected') != -1:
						print("Already connected!")
						return
					elif exception.find('Input/output error') != -1:
						print "Connman I/O error! Attempting to reset."
						self.reset()
						return
					else:
						print "WIFI ERROR!"
						print exception
						self.reset()
						return

	def setWifiPower(self,bState):
		tech = pyconnman.ConnTechnology('/net/connman/technology/wifi')
		if tech.get_property('Powered') == 0 and bState == True:
			tech.set_property('Powered', 1)
		elif tech.get_property('Powered') == 1 and bState == False:
			tech.set_property('Powered', 0)

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
					path = str(dbus.ObjectPath(path))
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

	def connect(self,ssidName,passphrase):
		if self.services == None:
			self.listServices()

		servicePath = None

		for (path, params) in self.services:
			if str(dbus.String(params['Name'])) == ssidName:
				bConnect = True
				servicePath = path
				try:
					agent = pyconnman.SimpleWifiAgent(path)
					agent.set_service_params(service=path, name=ssidName,passphrase=passphrase)
					self.manager.register_agent(path)
				except:
					pass
				break
		
		if servicePath:
			print "Attempting to connect to " + ssidName + "..."
			service = pyconnman.ConnService(servicePath)
			try:
				service.connect()
				self.service = service
			except dbus.exceptions.DBusException:
				exception = str(dbus.String(sys.exc_info()[1]))
				if exception.find('AlreadyConnected') != -1:
					pass
				else:
					print exception
		else:
				print("No wifi network found")
