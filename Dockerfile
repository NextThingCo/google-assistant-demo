# Base from Debian instead of Alpine, since Google uses glibc
FROM arm32v7/debian:stretch-slim
LABEL architecture="ARMv7"

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

RUN mkdir /APP && mkdir /APP/google-assistant

#COPY client.json /APP/google-assistant
#copy wifiSettings.json /APP/google-assistant
#COPY src/asoundrc /root/.asoundrc

# Install packages
RUN apt-get update && \

	apt-get install --no-install-recommends -y \
		build-essential \
		alsa-utils \
		libffi-dev \
		libssl-dev \
		locales \
		wget \
		tar \
		lsb zlib1g-dev \
		portaudio19-dev \
		python3-dev \
		python3-dbus \
		python3-pip

RUN locale-gen en_US en_US.UTF-8 && \
	sed -i -e "s/# $LANG.*/$LANG.UTF-8 UTF-8/" /etc/locale.gen && \
	dpkg-reconfigure --frontend=noninteractive locales && \
	update-locale LANG=$LANG && \

	pip3 install --upgrade pip setuptools && \
	pip3 install click && \
	pip3 install grpcio-tools && \
	pip3 install argparse && \
	pip3 install google-auth && \
	pip3 install google-assistant-grpc && \
	pip3 install urllib3[secure] && \
	pip3 install sounddevice && \
	pip3 install click && \
	pip3 install tenacity && \
	pip3 install pyconnman && \

	# Install Google SDK and other utils
	pip3 install --upgrade google-assistant-library && \
	pip3 install --upgrade google-auth-oauthlib[tool] && \

	mkdir -p /root/.config/google-oauthlib-tool

#RUN cd /tmp && wget https://github.com/pyinstaller/pyinstaller/releases/download/v3.2.1/PyInstaller-3.2.1.tar.bz2 && \
#	tar jxf PyInstaller-3.2.1.tar.bz2 && \
#	cd /tmp/Py*/bootloader && \
#	python3 ./waf distclean all --no-lsb option && cd /tmp/Py* && python3 setup.py install

COPY src/*.py /opt/

WORKDIR /opt
#RUN pyinstaller -D -F -n ntc-google-assistant -c test.py
#RUN ls /opt/
	
#	# Free up any extra space
#RUN pip3 freeze | xargs pip3 uninstall -y
#RUN  apt-get install -f && \#
#	apt-get remove --purge -y build-essential python3-pip lsb && \
#	apt-get autoremove -y && \
#	rm -rf /root/.cache && \
#	rm -rf /usr/share/sounds/alsa/*

#COPY ./src/*.py /APP/google-assistant/

COPY credentials.json /root/.config/google-oauthlib-tool/
COPY src/asoundrc /root/.asoundrc

#WORKDIR /APP/google-assistant
#ENTRYPOINT cp /opt/dist/ntc-google-assistant /tmp/


WORKDIR /opt
RUN apt-get install -y git && \
	git clone https://github.com/googlesamples/assistant-sdk-python

