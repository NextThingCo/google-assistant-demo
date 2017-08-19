#!/usr/bin/env python

import subprocess
import os.path
import sys

def is_chipPro():
	f = open("/proc/meminfo","r")
	fline = f.readline()
	f.close()
	parts = fline.split()
	mem = float(parts[1]) / 1024
	if mem <= 380:
		return True

if is_chipPro():
	subprocess.call('echo 49 > /sys/class/gpio/export', shell=True)
	subprocess.call('echo "out" > /sys/class/gpio/gpio49/direction', shell=True)
	subprocess.call('echo 1 > /sys/class/gpio/gpio49/value', shell=True)

# Check if we need to set up credentials first.
while os.path.exists('/root/.config/google-oauthlib-tool/credentials.json') == False:
	subprocess.call('google-oauthlib-tool --client-secrets /opt/client.json --scope https://www.googleapis.com/auth/assistant-sdk-prototype --save --headless', shell=True)

#p = Popen('google-assistant-demo', stdout = PIPE, stderr = STDOUT, shell = True)
subprocess.call('google-assistant-demo', shell=True)
