#!/usr/bin/env python

import subprocess
import os.path
import socket
import time
import sys

# Turn on external UFL antenna for optimal wifi signal strength.
subprocess.call('echo 49 > /sys/class/gpio/export', shell=True)
subprocess.call('echo "out" > /sys/class/gpio/gpio49/direction', shell=True)
subprocess.call('echo 1 > /sys/class/gpio/gpio49/value', shell=True)

def is_connected():
	try:
		host = socket.gethostbyname('www.google.com')
		s = socket.create_connection((host, 80), 2)
		return True
	except:
		pass
		return False

sys.stderr.write("Google Assistant is starting...\n")

bPlayedNetSound = False
bPlayedIntroSound = False
bIsRunning = True
subprocess.call('amixer sset "Master" 80%', shell=True)
subprocess.call('mpg123 /opt/wait.mp3 --buffer size=3072', shell=True)

while bIsRunning:
	while is_connected() == False:
		time.sleep(3)
		if bPlayedNetSound == False:
			bPlayedNetSound = True
			subprocess.call('mpg123 /opt/net.mp3 --buffer size=3072', shell=True)

		sys.stderr.write("Waiting for internet...\n")

	sys.stderr.write("Internet connection established. Starting application...\n")

	if bPlayedNetSound == True:
		subprocess.call('mpg123 /opt/wait.mp3 --buffer size=3072', shell=True)

	bPlayedNetSound = False
	if bPlayedIntroSound == False:
		bPlayedIntroSound = True
		subprocess.Popen('sleep 4;mpg123 /opt/intro.mp3 --buffer size=3072;amixer sset "Master" 100%', shell=True)

	# Fix for possible grpc issues regarding bad security handshakes
	subprocess.call('ulimit -n 65536', shell=True)
	subprocess.call('google-assistant-demo', shell=True)
