from pydispatch import dispatcher
import pyconnman
import dbus
import dbus.mainloop.glib
import threading
import gobject
import time
import socket
import sys
import subprocess
import os

STATUS_DISCONNECTED		= "disconnected" 	# Not connected to any wifi network
STATUS_REJECTION		= "rejected"		# Connection attempt was refused. Possibly bad password.
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

		self.waitForWifiInterface()
		self.setWifiPower(True)
		self.listServices()

		def update():
			while True:
				print self.getStatus()
				time.sleep(4)

		t = threading.Thread(target=update, args = ())
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
				
			time.sleep(0.5)

	def getStatus(self):
		status = STATUS_DISCONNECTED
		try:
			if self.manager.get_property(name='State') != "idle":
				#print "socket?"
				#socket.setdefaulttimeout(NETWORK_TIMEOUT)
				#socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(('8.8.8.8', 53))
				status = STATUS_ONLINE
				return true
			else:
				print self.manager.get_property(name='State')
				print "reconnnect"
				self.reconnect()
		except:
			pass
	
		return self.setStatus(status)

	def setStatus(self,status):
		if self.status != status:
			dispatcher.send(signal="wifi_connection_status",statusID=self.status)
			
		self.status = status
		return self.status

	# Check if an agent has already been set up for an access point with the specified path.
	def agentExists(self,path):
		agents = os.listdir('/var/lib/connman')
		for agent in agents:
			if path == '/net/connman/service/'+agent:
				return True

		return False

	def reset(self):
		#self.setWifiPower(False)
		subprocess.call(['rfkill','block','1'],stdout=FNULL)
		subprocess.call(['rfkill','unblock','1'],stdout=FNULL)
		self.setWifiPower(True)
		self.waitForWifiInterface()
		self.listServices()

	# Attempt to reconnect to a previous wifi agent
	def reconnect(self):
		for (path, params) in self.services:
			if self.agentExists(path):
				print ("Attempting to reconnect to " + params['Name'])
				self.connect(params['Name'],None)
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
		print tech
		print tech.get_property('Powered')
		if tech.get_property('Powered') == 0 and bState == True:
			print "SET IT"
			tech.set_property('Powered', 1)
			print tech.get_property('Powered')
		elif tech.get_property('Powered') == 1 and bState == False:
			print "FORGET IT"
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

	def connect(self,ssidName,passphrase):
		if self.services == None:
			self.listServices()

		servicePath = None

		for (path, params) in self.services:
			try:
				if str(dbus.String(params['Name'])) == ssidName:
					bConnect = True
					servicePath = path
					agent = pyconnman.SimpleWifiAgent(path)
					agent.set_service_params(service=path, name=ssidName,passphrase=passphrase)
					self.manager.register_agent(path)
					break
			except:
				pass
		
		if servicePath:
			print "Attempting to connect to " + ssidName + "..."
			service = pyconnman.ConnService(servicePath)
			try:
				service.connect()
				self.service = service
			except dbus.exceptions.DBusException:
				
				exception = str(dbus.String(sys.exc_info()[1]))
				print exception
				if exception.find('AlreadyConnected') != -1:
					pass
				elif exception.find('NoReply') != -1:
					dispatcher.send(signal="wifi_connection_status",statusID=STATUS_REJECTION)
		else:
				print("No wifi network found")
