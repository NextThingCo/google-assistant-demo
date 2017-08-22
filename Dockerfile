# Base from Debian instead of Alpine, since Google uses glibc
FROM arm32v7/debian:stretch-slim
LABEL architecture="ARMv7"

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

RUN mkdir /APP && mkdir /APP/google-assistant

COPY client.json /APP/google-assistant
#copy wifiSettings.json /APP/google-assistant
COPY src/asoundrc /root/.asoundrc

# Install packages
RUN apt-get update && \

	apt-get install --no-install-recommends -y \
		build-essential \
		alsa-utils \
		libffi-dev \
		libssl-dev \
		locales \
		python-dev \
		python-dbus \
		python-pip && \

	# Set locales
	locale-gen en_US en_US.UTF-8 && \
	sed -i -e "s/# $LANG.*/$LANG.UTF-8 UTF-8/" /etc/locale.gen && \
	dpkg-reconfigure --frontend=noninteractive locales && \
	update-locale LANG=$LANG && \

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

	# Install Google SDK and other utils
	pip install --upgrade google-assistant-library && \
	pip install --upgrade google-auth-oauthlib[tool] && \

	## Install pyconnman and fix Python3 specific issues
	#export PYCONPATH=/usr/local/lib/python3.5/dist-packages/pyconnman && \
	#pip3 install --upgrade pyconnman && \
	#sed -i 's/from exceptions/from pyconnman.exceptions/' $PYCONPATH/interface.py && \
	#sed -i 's/from exceptions/from pyconnman.exceptions/' $PYCONPATH/agent.py && \
	#sed -i 's/from interface/from pyconnman.interface/' $PYCONPATH/service.py && \
	#sed -i 's/from interface/from pyconnman.interface/' $PYCONPATH/manager.py && \
	#sed -i 's/from interface/from pyconnman.interface/' $PYCONPATH/technology.py && \

	mkdir -p /root/.config/google-oauthlib-tool && \
#	mkdir /APP/wifi && \

	apt-get remove -y --purge build-essential && \

	# Free up any extra space
	rm -rf /root/.cache && \
	rm -rf /usr/share/sounds/alsa/* 

#ADD wifi-onboarding/start.sh /APP/wifi/start.sh
#ADD build/linux_arm/wifi-onboarding /APP/wifi/wifi-onboarding
#ADD wifi-onboarding/static /APP/wifi/static
#ADD wifi-onboarding/view /APP/wifi/view

#ADD wifi-onboarding/hostapd.conf /etc/hostapd.conf
#ADD wifi-onboarding/dnsmasq.conf /etc/dnsmasq.conf

COPY ./src/start.py /APP/google-assistant/
COPY ./src/test.py /APP/google-assistant/

WORKDIR /APP

CMD ["/bin/sh"]
#CMD ["python3", "/opt/start.py"]
