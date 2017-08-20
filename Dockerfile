# Base from Debian instead of Alpine, since Google uses glibc
FROM arm32v7/debian:stretch-slim
LABEL architecture="ARMv7"

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

COPY client.json /opt/
copy wifiSettings.json /opt/
COPY src/asoundrc /root/.asoundrc

# Install packages
RUN apt-get update && \

	apt-get install --no-install-recommends -y \
		alsa-utils \
		locales \
		connman \
		python3-dev \
		python3-dbus \
		python3-pip && \

	# Set locales
	locale-gen en_US en_US.UTF-8 && \
	sed -i -e "s/# $LANG.*/$LANG.UTF-8 UTF-8/" /etc/locale.gen && \
	dpkg-reconfigure --frontend=noninteractive locales && \
	update-locale LANG=$LANG && \

	pip3 install --upgrade pip setuptools && \

	# Install Google SDK and other utils
	pip3 install --upgrade google-assistant-library && \
	pip3 install --upgrade google-auth-oauthlib[tool] && \

	# Install pyconnman and fix Python3 specific issues
	export PYCONPATH=/usr/local/lib/python3.5/dist-packages/pyconnman && \
	pip3 install --upgrade pyconnman && \
	sed -i 's/from exceptions/from pyconnman.exceptions/' $PYCONPATH/interface.py && \
	sed -i 's/from exceptions/from pyconnman.exceptions/' $PYCONPATH/agent.py && \
	sed -i 's/from interface/from pyconnman.interface/' $PYCONPATH/service.py && \
	sed -i 's/from interface/from pyconnman.interface/' $PYCONPATH/manager.py && \
	sed -i 's/from interface/from pyconnman.interface/' $PYCONPATH/technology.py && \

	mkdir -p /root/.config/google-oauthlib-tool && \

	# Free up any extra space
	rm -rf /root/.cache && \
	rm -rf /usr/share/sounds/alsa/* 

COPY /src/start.py /opt/

CMD ["python3", "/opt/start.py"]
#ENTRYPOINT ulimit -n 65536 && python3 /opt/start.py
#ENTRYPOINT  ulimit -n 65536 && /bin/sh
