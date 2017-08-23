FROM armhf/alpine
LABEL architecture="ARMv7"

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

RUN mkdir /APP && mkdir /APP/google-assistant

COPY client.json /APP/google-assistant
#copy wifiSettings.json /APP/google-assistant
COPY src/asoundrc /root/.asoundrc

# Install packages
RUN apk update && \

	apk add --no-cache \
		gcc make g++ zlib-dev \
		alsa-utils \
		libffi-dev \
		libressl-dev \
		python2-dev \
		py-dbus \
		py2-pip && \

	pip install --upgrade pip setuptools && \
	pip install click && \
	pip install grpcio-tools && \
	pip install argparse && \
	pip install google-auth && \
	pip install google-assistant-grpc && \
	pip install urllib3[secure] && \
	pip install sounddevice && \
	pip install click && \
	pip install tenacity && \
	pip install pyconnman && \

	# Install Google SDK and other utils
	pip install --upgrade google-assistant-library && \
	pip install --upgrade google-auth-oauthlib[tool] && \

	mkdir -p /root/.config/google-oauthlib-tool && \

	apk del gcc make g++ zlib-dev && \

	# Free up any extra space
	rm -rf /root/.cache && \
	rm -rf /usr/share/sounds/alsa/*

COPY ./src/*.py /APP/google-assistant/

RUN apk add --no-cache libstdc++ libc6-compat portaudio

WORKDIR /APP/google-assistant

CMD ["/bin/sh"]
