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

import dbus.mainloop.glib
import subprocess
import threading
import pexpect
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

NETWORK_TIMEOUT			= 3					# Number of seconds to give up on trying to the internet

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
gobject.threads_init()

class WifiManager():
	def __init__(self):
		self.manager = pyconnman.ConnManager()
		self.bInternetConnected = False
		self.status = STATUS_DISCONNECTED
		self.agent = None
		self.services = None

		self.waitForWifiInterface()
		self.setWifiPower(True)
		time.sleep(1)
		self.reset()

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
		if state == "online" or status == "ready":
			# Ping Google to see if we have an internet connection.
			try:
				urllib2.urlopen('http://216.58.192.142', timeout=NETWORK_TIMEOUT)
				self.bInternetConnected = True
				status = STATUS_ONLINE
			except:
				self.bInternetConnected = False
				status = STATUS_OFFLINE

		# If not connected to any wifi network...
		elif state == "idle" and self.status != self.bInternetConnected:
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
		self.setWifiPower(True)
		self.waitForWifiInterface()
		self.listServices()

	# Check if an agent has already been set up for an access point with the specified path.
	def agentExists(self,path):
		agents = os.listdir('/var/lib/connman')
		for agent in agents:
			if path == agent:
				return True

		return False

	# Evaluate if any previous wifi network we've connected to is currently in range.
	def checkPreviousWifiNetworks(self):
		if self.services == None:
			self.listServices()

		for (path, params) in self.services:
			if self.agentExists(path):
				return True

		return False

	# Attempt to reconnect to a previous wifi agent
	def reconnect(self):
		if self.services == None:
			self.listServices()
			return

		for (path, params) in self.services:
			wifiPath = path.replace('/net/connman/service/','')
			settingsFile = '/var/lib/connman/'+wifiPath+'/settings'
			if self.agentExists(wifiPath) and os.path.isfile(settingsFile) and 'Favorite=true' in open(settingsFile).read():
				print ("Attempting to reconnect to " + params['Name'])
				self.connect(servicePath=wifiPath)

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
			print tech
			try:
				tech.scan()
			except:
				# The carrier might not be ready yet if wifi is still powering on
				return

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

	def connect(self,servicePath=None,ssid=None,passphrase=None,name=None,identity=None,username=None,password=None,wpspin=None):
		print "connect1"

		while self.services == None:
			self.listServices()
			time.sleep(0.5)

		print "connect2"
		bClear = False
		if not servicePath and ssid:
			print "connect3"
			for (path, params) in self.services:
				try:
					if str(dbus.String(params['Name'])) == ssid:
						servicePath = path
						bClear = True
						print "connect3"
				except:
					pass

			if not servicePath:
				print("No wifi network found")
				return

			print "connect4"
			
			if os.path.exists('/var/lib/connman/'+servicePath):
				os.system('rm -rf /var/lib/connman/'+servicePath)

			print "Attempting to connect to " + ssid + "..." + passphrase
		
		print "connect5"

		self.setStatus(STATUS_CONNECTING)
		
		child = pexpect.spawn('connmanctl')
		child.expect('connmanctl>')

		servicePath = servicePath.replace('/net/connman/service/','')

		if bClear:
			child.sendline('config ' + servicePath + ' --remove')

		child.sendline('agent on')
		child.expect('connmanctl>')
		child.sendline('connect ' + servicePath)

		def doConnect():
			print "connect6"
			try:
				index = child.expect(['.*Already.*','.*Connected.*','.*Passphrase.*','.*In progress.*','.*Input/output.*','.*invalid.*','.*try (yes/no).*','.*aborted.*'], timeout=20)
				print child.after
				if index == 0 or index == 1:
					print "ONLINE"
					self.setStatus(STATUS_ONLINE)
				elif index == 2:
					child.sendline(passphrase)
					doConnect()
				elif index == 3 or index == 4:
					time.sleep(2)
					doConnect()
				elif index == 5 or index == 6:
					self.setStatus(STATUS_REJECTION)
				else:
					time.sleep(6)
					child.sendline('connect ' + servicePath)
					doConnect()
			except:
				print "timeout"
				if not self.bInternetConnected:
					self.reconnect()
				else:
					self.setStatus(STATUS_ONLINE)

		print "connect?"
		doConnect()
		print "connect!"
		child.close()