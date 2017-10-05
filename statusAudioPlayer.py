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

import subprocess
import threading
import psutil
import time

ASSISTANT_LISTENING_AUDIO 		= "resources/chime.wav"
ASSISTANT_FAILURE_AUDIO 		= "resources/unsuccessful.wav"

INTRO_AUDIO 					= "resources/instructions.wav"
WAIT_AUDIO						= "resources/wait.wav"
THINKING_AUDIO					= "resources/thinking.wav"
READY_AUDIO						= "resources/ready.wav"
INTERNET_DISCONNECTED 			= "resources/internet_disconnected.wav"

SETUP_AUDIO_PART1				= "resources/setup-1.wav"	# Intructions before saying IP address
SETUP_AUDIO_PART2_1				= "resources/setup-2_1.wav"	# For 192.168.81.1
SETUP_AUDIO_PART2_2				= "resources/setup-2_2.wav"	# For 192.168.81.2
SETUP_AUDIO_PART3				= "resources/setup-3.wav"	# Instructions after saying IP address
SETUP_AUDIO_PART4				= "resources/setup-4.wav"	# Repeated instruction


class StatusAudioPlayer():
	def __init__(self):
		self.bPlayedIntro = False
		self.bPlayedSetupInstructions = False
		self.audioHighPriorityProcs = 0
		self.bUserConnectedToWebFrontend = False
		self.introTime = -100
		self.audioTime = -100

	# Set a status value for whether or not the user has successfully connected to the local web server's HTML frontend.
	def setUserConnectionStatus(self,bStatus):
		self.bUserConnectedToWebFrontend = bStatus

	# Use aplay to play a WAV audio file with a specified priority and any delay.
	# Can also set to block. Otherwise, aplay will run in its own thread.
	def playAudio(self,audioFile,bBlocking=False,bPriority=False,delay=0):
		# If this audio file is not high priority and one is already playing, do nothing.
		if not bPriority and self.highPriorityAudioIsPlaying(): return
		if delay > 0 and time.time() - self.audioTime < 0.5: return

		
		def aplay():
			self.audioTime = time.time()
			if bPriority: self.audioHighPriorityProcs = self.audioHighPriorityProcs + 1
			cmd = "sleep " + str(delay) + " && aplay --period-size=8192 --buffer-size=32768 --quiet " + audioFile
			subprocess.call(cmd,shell=True)
			if bPriority: self.audioHighPriorityProcs = self.audioHighPriorityProcs - 1

		if not bBlocking:
			t = threading.Thread(target=aplay, args = ())
			t.setDaemon(True)
			t.start()
		else:
			aplay()

		return

	def killAll(self):
		for proc in psutil.process_iter():
			if proc.name() == 'aplay':
				proc.kill()

	def highPriorityAudioIsPlaying(self):
		if self.audioHighPriorityProcs > 0:
			return True
		else:
			return False

	def playIntro(self):
		if not self.bPlayedIntro:
			self.introTime = time.time()
			self.bPlayedIntro = True
			self.playAudio(INTRO_AUDIO,delay=1,bPriority=True)
			time.sleep(1.5)
		else:
			self.playAudio(WAIT_AUDIO,delay=1.5,bPriority=False)

	def playSetupInstructions(self):		
		if self.bPlayedSetupInstructions:
			return

		self.bPlayedSetupInstructions = True
		# The USB ethernet gadget will either use 192.168.81.1 or 192.168.82.1, depending on the client's OS.
		# Return true if 81.1, or false if 82.1
		def getIPAudio():
			status = None
			while not status:
				try:
					status = subprocess.check_output(['ip','a','show','usb0'])
				except:
					pass

			if status.find('NO-CARRIER') > -1:
				return SETUP_AUDIO_PART2_2

			return SETUP_AUDIO_PART2_1

		def audioSequence():
			time.sleep(0.5)
			self.playAudio(SETUP_AUDIO_PART1, bBlocking=True,bPriority=True)
			# Play specific files for a USB IP address for 192.168.81.1 and another for 192.168.82.1
			self.playAudio(getIPAudio(), bBlocking=True,bPriority=True)
			reminders = 0

			# If user has not yet connected to the web server HTML frontend, play the IP address audio again.
			while not self.bUserConnectedToWebFrontend:
				if reminders == 0:
					time.sleep(1)
					self.audioMessagePriorityProc = self.playAudio(SETUP_AUDIO_PART3,bBlocking=True,bPriority=True)
				else:
					time.sleep(10)
					self.audioMessagePriorityProc = self.playAudio(SETUP_AUDIO_PART4,bBlocking=True,bPriority=True)

				self.audioMessagePriorityProc = self.playAudio(getIPAudio(), bBlocking=True,bPriority=True)

				reminders = reminders+1
				if reminders > 5:
					return

		t = threading.Thread(target=audioSequence, args = ())
		t.setDaemon(True)
		t.start()

	def playThinking(self,delay=0):
		self.playAudio(THINKING_AUDIO,delay=delay)

	def playDisconnected(self):
		time.sleep(0.25)
		self.playAudio(INTERNET_DISCONNECTED)
		self.playAudio(THINKING_AUDIO,delay=2)

	def playWait(self):
		time.sleep(0.25)
		self.playAudio(WAIT_AUDIO)	

	def playReadyAudio(self):
		time.sleep(0.25)
		if self.introTime and time.time() - self.introTime < 30:
			return

		self.playAudio(READY_AUDIO)

	def playListeningAudio(self):
		self.playAudio(ASSISTANT_LISTENING_AUDIO)

	def playFailureAudio(self):
		self.playAudio(ASSISTANT_FAILURE_AUDIO)
