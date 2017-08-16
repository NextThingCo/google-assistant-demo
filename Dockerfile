FROM arm32v7/debian:stretch-slim
LABEL architecture="ARMv7"

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

# Install packages
RUN apt-get update && \
	apt-get install --no-install-recommends -y \
		alsa-utils \
		gcc \
		python3-dev \
		python3-pip \
		portaudio19-dev \
		libffi-dev \
		libssl-dev && \

	# Install and set python
	pip3 install pip setuptools --upgrade && \

	# Install google-assistant-sdk
	pip3 -v install --upgrade https://github.com/googlesamples/assistant-sdk-python/releases/download/0.3.0/google_assistant_library-0.0.2-py2.py3-none-linux_armv7l.whl && \
	pip3 install google-assistant-sdk[samples] && \

	apt-get remove -y --purge gcc build-essential python3-pip && \
	rm -rf /var/lib/apt/lists/*

COPY *.json /tmp/
RUN mv /tmp/*.json /opt/client.json
	
ENTRYPOINT echo "\n###############\nTo authorize, run this command:\n\ngoogle-oauthlib-tool --client-secrets /opt/client.json --scope https://www.googleapis.com/auth/assistant-sdk-prototype --save\n\n" && \
	echo "To start, run:\n\ngoogle-assistant-demo\n\n" && \
	/bin/sh

