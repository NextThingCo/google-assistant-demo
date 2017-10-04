# Copyright (C) 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Sample that implements gRPC client for Google Assistant API."""

# pip install google-assistant-library

from google.rpc import code_pb2
from google.assistant.library import Assistant
from google.assistant.library.event import EventType
from google.assistant.embedded.v1alpha1 import embedded_assistant_pb2
from tenacity import retry, stop_after_attempt, retry_if_exception



import os
import grpc
import json
import google.auth.transport.grpc
import google.auth.transport.requests
import google.oauth2.credentials
import sounddevice
import threading
import time
import wave
import math
import array

from assistantManager import GoogleAssistantAuthorization

CREDENTIALS = '/opt/.config/credentials.json'
ASSISTANT_API_ENDPOINT = 'embeddedassistant.googleapis.com'
END_OF_UTTERANCE = embedded_assistant_pb2.ConverseResponse.END_OF_UTTERANCE
DIALOG_FOLLOW_ON = embedded_assistant_pb2.ConverseResult.DIALOG_FOLLOW_ON
CLOSE_MICROPHONE = embedded_assistant_pb2.ConverseResult.CLOSE_MICROPHONE
DEFAULT_GRPC_DEADLINE = 60 * 3 + 5

DEFAULT_AUDIO_SAMPLE_RATE = 16000
DEFAULT_AUDIO_SAMPLE_WIDTH = 2
DEFAULT_AUDIO_ITER_SIZE = 3200
DEFAULT_AUDIO_DEVICE_BLOCK_SIZE = 6400
DEFAULT_AUDIO_DEVICE_FLUSH_SIZE = 25600

DEFAULT_ULIMIT = 65536

class SampleAssistant(object):
	#Sample Assistant that supports follow-on conversations.

	def __init__(self):
		verbose = False
		http_request = None
		credsObj = None
		self.previousEvent = None

		if not os.path.exists('/opt/.config'):
			os.makedirs('/opt/.config')

		os.system('ulimit -n ' + str(DEFAULT_ULIMIT))

		self.auth = GoogleAssistantAuthorization()

		if self.auth.bNeedAuthorization == True and self.auth.checkCredentials() == False:
			return

		# Load OAuth 2.0 credentials.
		try:
			with open(CREDENTIALS, 'r') as f:
				credsObj = google.oauth2.credentials.Credentials(token=None,**json.load(f))
				http_request = google.auth.transport.requests.Request()
				credsObj.refresh(http_request)
		except Exception as e:
			return

		with open(CREDENTIALS, 'r') as f:
			credsObj = google.oauth2.credentials.Credentials(token=None,
																**json.load(f))

		# Create an authorized gRPC channel.
		grpc_channel = google.auth.transport.grpc.secure_authorized_channel(
			credsObj, http_request, ASSISTANT_API_ENDPOINT)

		self.conversation_state = None

		# Create Google Assistant API gRPC client.
		self.assistant = embedded_assistant_pb2.EmbeddedAssistantStub(grpc_channel)
		self.deadline = DEFAULT_GRPC_DEADLINE

		# Configure audio source and sink.
		audio_device = None

		audio_source = audio_device = (
			audio_device or SoundDeviceStream(
				sample_rate=DEFAULT_AUDIO_SAMPLE_RATE,
				sample_width=DEFAULT_AUDIO_SAMPLE_WIDTH,
				block_size=DEFAULT_AUDIO_DEVICE_BLOCK_SIZE,
				flush_size=DEFAULT_AUDIO_DEVICE_FLUSH_SIZE
			)
		)
		audio_sink = audio_device = (
			audio_device or SoundDeviceStream(
				sample_rate=DEFAULT_AUDIO_SAMPLE_RATE,
				sample_width=DEFAULT_AUDIO_SAMPLE_WIDTH,
				block_size=DEFAULT_AUDIO_DEVICE_BLOCK_SIZE,
				flush_size=DEFAULT_AUDIO_DEVICE_FLUSH_SIZE
			)
		)
		# Create conversation stream with the given audio source and sink.
		self.conversation_stream = ConversationStream(
			source=audio_source,
			sink=audio_sink,
			iter_size=DEFAULT_AUDIO_ITER_SIZE,
			sample_width=DEFAULT_AUDIO_SAMPLE_WIDTH,
		)

		hotword = Assistant(credsObj)

		with self:
			for event in hotword.start():
				self.process_event(event)

			while True:
				continue_conversation = assistant.converse()

				# If we only want one conversation, break.
				if not continue_conversation:
					break

	def __enter__(self):
		return self

	def __exit__(self, etype, e, traceback):
		if e:
			return False
		self.conversation_stream.close()

	def set_active(self,bActive):
		self.bActive = bActive

	def process_event(self,event):
		dispatcher.send(signal='google_assistant_event',eventName=event.type)
		self.previousEvent = event.type

		if event.type == EventType.ON_CONVERSATION_TURN_STARTED:
			print()

		print(event)

		if (event.type == EventType.ON_CONVERSATION_TURN_FINISHED and
				event.args and not event.args['with_follow_on_turn']):
			print()

	def get_previous_event(self):
		return self.previousEvent

	def is_grpc_error_unavailable(e):
		is_grpc_error = isinstance(e, grpc.RpcError)
		if is_grpc_error and (e.code() == grpc.StatusCode.UNAVAILABLE):
			print('grpc unavailable error: ' + str(e))
			return True
		return False

	@retry(reraise=True, stop=stop_after_attempt(3),
		   retry=retry_if_exception(is_grpc_error_unavailable))
	def converse(self):
		"""Send a voice request to the Assistant and playback the response.

		Returns: True if conversation should continue.
		"""
		continue_conversation = False

		self.conversation_stream.start_recording()

		def iter_converse_requests():
			for c in self.gen_converse_requests():
				#print(c)
				#assistant_helpers.log_converse_request_without_audio(c)
				yield c
			self.conversation_stream.start_playback()

		# This generator yields ConverseResponse proto messages
		# received from the gRPC Google Assistant API.
		for resp in self.assistant.Converse(iter_converse_requests(),
											self.deadline):
			self.process_event(resp.event)
			#print(resp)
			#assistant_helpers.log_converse_response_without_audio(resp)
			if resp.error.code != code_pb2.OK:
				print('server error: ' + str(resp.error.message))
				break
			if resp.event_type == END_OF_UTTERANCE:
				self.conversation_stream.stop_recording()
			if resp.result.spoken_request_text:
				print('Transcript of user request: ' + resp.result.spoken_request_text)
			if len(resp.audio_out.audio_data) > 0:
				self.conversation_stream.write(resp.audio_out.audio_data)
			if resp.result.spoken_response_text:
				print('Transcript of TTS response: ' + rresp.result.spoken_response_text)
			if resp.result.conversation_state:
				self.conversation_state = resp.result.conversation_state
			if resp.result.volume_percentage != 0:
				self.conversation_stream.volume_percentage = resp.result.volume_percentage
			if resp.result.microphone_mode == DIALOG_FOLLOW_ON:
				continue_conversation = True
			elif resp.result.microphone_mode == CLOSE_MICROPHONE:
				continue_conversation = False
		self.conversation_stream.stop_playback()
		return continue_conversation

	def gen_converse_requests(self):
		converse_state = None
		if self.conversation_state:
			converse_state = embedded_assistant_pb2.ConverseState(
				conversation_state=self.conversation_state,
			)
		config = embedded_assistant_pb2.ConverseConfig(
			audio_in_config=embedded_assistant_pb2.AudioInConfig(
				encoding='LINEAR16',
				sample_rate_hertz=self.conversation_stream.sample_rate,
			),
			audio_out_config=embedded_assistant_pb2.AudioOutConfig(
				encoding='LINEAR16',
				sample_rate_hertz=self.conversation_stream.sample_rate,
				volume_percentage=self.conversation_stream.volume_percentage,
			),
			converse_state=converse_state
		)
		# The first ConverseRequest must contain the ConverseConfig
		# and no audio data.
		yield embedded_assistant_pb2.ConverseRequest(config=config)
		for data in self.conversation_stream:
			# Subsequent requests need audio data, but not config.
			yield embedded_assistant_pb2.ConverseRequest(audio_in=data)

class WaveSource(object):
	"""Audio source that reads audio data from a WAV file.

	Reads are throttled to emulate the given sample rate and silence
	is returned when the end of the file is reached.

	Args:
	  fp: file-like stream object to read from.
	  sample_rate: sample rate in hertz.
	  sample_width: size of a single sample in bytes.
	"""
	def __init__(self, fp, sample_rate, sample_width):
		self._fp = fp
		try:
			self._wavep = wave.open(self._fp, 'r')
		except wave.Error as e:
			self._fp.seek(0)
			self._wavep = None

		self._sample_rate = sample_rate
		self._sample_width = sample_width
		self._sleep_until = 0

	def read(self, size):
		#Read bytes from the stream and block until sample rate is achieved.
		now = time.time()
		missing_dt = self._sleep_until - now
		if missing_dt > 0:
			time.sleep(missing_dt)
		self._sleep_until = time.time() + self._sleep_time(size)
		data = (self._wavep.readframes(size)
				if self._wavep
				else self._fp.read(size))
		#  When reach end of audio stream, pad remainder with silence (zeros).
		if not data:
			return b'\x00' * size
		return data

	def close(self):
		"""Close the underlying stream."""
		if self._wavep:
			self._wavep.close()
		self._fp.close()

	def _sleep_time(self, size):
		sample_count = size / float(self._sample_width)
		sample_rate_dt = sample_count / float(self._sample_rate)
		return sample_rate_dt

	def start(self):
		pass

	def stop(self):
		pass

	@property
	def sample_rate(self):
		return self._sample_rate


class WaveSink(object):
	"""Audio sink that writes audio data to a WAV file.

	Args:
	  fp: file-like stream object to write data to.
	  sample_rate: sample rate in hertz.
	  sample_width: size of a single sample in bytes.
	"""
	def __init__(self, fp, sample_rate, sample_width):
		self._fp = fp
		self._wavep = wave.open(self._fp, 'wb')
		self._wavep.setsampwidth(sample_width)
		self._wavep.setnchannels(1)
		self._wavep.setframerate(sample_rate)

	def write(self, data):
		"""Write bytes to the stream.

		Args:
		  data: frame data to write.
		"""
		self._wavep.writeframes(data)

	def close(self):
		"""Close the underlying stream."""
		self._wavep.close()
		self._fp.close()

	def start(self):
		pass

	def stop(self):
		pass


class SoundDeviceStream(object):
	"""Audio stream based on an underlying sound device.

	It can be used as an audio source (read) and a audio sink (write).

	Args:
	  sample_rate: sample rate in hertz.
	  sample_width: size of a single sample in bytes.
	  block_size: size in bytes of each read and write operation.
	  flush_size: size in bytes of silence data written during flush operation.
	"""
	def __init__(self, sample_rate, sample_width, block_size, flush_size):
		if sample_width == 2:
			audio_format = 'int16'
		else:
			raise Exception('unsupported sample width:', sample_width)
		self._audio_stream = sounddevice.RawStream(
			samplerate=sample_rate, dtype=audio_format, channels=1,
			blocksize=int(block_size/2),  # blocksize is in number of frames.
		)
		self._block_size = block_size
		self._flush_size = flush_size
		self._sample_rate = sample_rate

	def read(self, size):
		"""Read bytes from the stream."""
		buf, overflow = self._audio_stream.read(size)
		return bytes(buf)

	def write(self, buf):
		"""Write bytes to the stream."""
		underflow = self._audio_stream.write(buf)
		return len(buf)

	def flush(self):
		if self._flush_size > 0:
			self._audio_stream.write(b'\x00' * self._flush_size)

	def start(self):
		"""Start the underlying stream."""
		if not self._audio_stream.active:
			self._audio_stream.start()

	def stop(self):
		"""Stop the underlying stream."""
		if self._audio_stream.active:
			self.flush()
			self._audio_stream.stop()

	def close(self):
		"""Close the underlying stream and audio interface."""
		if self._audio_stream:
			self.stop()
			self._audio_stream.close()
			self._audio_stream = None

	@property
	def sample_rate(self):
		return self._sample_rate


class ConversationStream(object):
	"""Audio stream that supports half-duplex conversation.

	A conversation is the alternance of:
	- a recording operation
	- a playback operation

	  When conversations are finished:
	  - close()

	Args:
	  source: file-like stream object to read input audio bytes from.
	  sink: file-like stream object to write output audio bytes to.
	  iter_size: read size in bytes for each iteration.
	  sample_width: size of a single sample in bytes.
	"""
	def __init__(self, source, sink, iter_size, sample_width):
		self._source = source
		self._sink = sink
		self._iter_size = iter_size
		self._sample_width = sample_width
		self._stop_recording = threading.Event()
		self._start_playback = threading.Event()

	def start_recording(self):
		"""Start recording from the audio source."""
		self._stop_recording.clear()
		self._source.start()
		self._sink.start()

	def stop_recording(self):
		"""Stop recording from the audio source."""
		self._stop_recording.set()

	def start_playback(self):
		"""Start playback to the audio sink."""
		self._start_playback.set()

	def stop_playback(self):
		"""Stop playback from the audio sink."""
		self._start_playback.clear()
		self._source.stop()
		self._sink.stop()

	@property
	def volume_percentage(self):
		"""The current volume setting as an integer percentage (1-100)."""
		try:
			return self._volume_percentage
		except:
			return

	def read(self, size):
		"""Read bytes from the source (if currently recording).
		Will returns an empty byte string, if stop_recording() was called.
		"""
		if self._stop_recording.is_set():
			return b''
		return self._source.read(size)

	def write(self, buf):
		"""Write bytes to the sink (if currently playing).
		Will block until start_playback() is called.
		"""
		self._start_playback.wait()
		buf = self.align_buf(buf, self._sample_width)
		buf = self.normalize_audio_buffer(buf)
		return self._sink.write(buf)

	def normalize_audio_buffer(self, buf, volume_percentage=100, sample_width=2):
		if sample_width != 2:
			raise Exception('unsupported sample width:', sample_width)
		scale = math.pow(2, 1.0*volume_percentage/100)-1
		# Construct array from bytes based on sample_width, multiply by scale
		# and convert it back to bytes
		arr = array.array('h', buf)
		for idx in range(0, len(arr)):
			arr[idx] = int(arr[idx]*scale)
		buf = arr.tostring()
		return buf

	def align_buf(self, buf, sample_width):
		"""In case of buffer size not aligned to sample_width pad it with 0s"""
		remainder = len(buf) % sample_width
		if remainder != 0:
			buf += b'\0' * (sample_width - remainder)
		return buf

	def close(self):
		"""Close source and sink."""
		self._source.close()
		self._sink.close()

	def __iter__(self):
		"""Returns a generator reading data from the stream."""
		return iter(lambda: self.read(self._iter_size), b'')

	@property
	def sample_rate(self):
		return self._source._sample_rate

if __name__ == '__main__':
	assistant = SampleAssistant()