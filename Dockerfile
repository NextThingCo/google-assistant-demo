# Base from Debian instead of Alpine, since Google uses glibc
FROM arm32v7/debian:stretch-slim
LABEL architecture="ARMv7"

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

COPY client.json /opt/
COPY credentials.json /data/.config/google-oauthlib-tool/
COPY src/asoundrc /root/.asoundrc

# Install packages
RUN apt-get update && \

	apt-get install --no-install-recommends -y \
		mpg123 \
		alsa-utils \
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

	# Install Google SDK and other utils
	pip install --upgrade google-assistant-library && \
	pip install --upgrade google-auth-oauthlib[tool] && \

	# Install pyconnman and fix Python3 specific issues
	#export PYCONPATH=/usr/local/lib/python3.5/dist-packages/pyconnman && \
	#pip install --upgrade pyconnman && \
	#sed -i 's/from exceptions/from pyconnman.exceptions/' $PYCONPATH/interface.py && \
	#sed -i 's/from exceptions/from pyconnman.exceptions/' $PYCONPATH/agent.py && \
	#sed -i 's/from interface/from pyconnman.interface/' $PYCONPATH/service.py && \
	#sed -i 's/from interface/from pyconnman.interface/' $PYCONPATH/manager.py && \
	#sed -i 's/from interface/from pyconnman.interface/' $PYCONPATH/technology.py && \

	mkdir -p /root/.config/google-oauthlib-tool && \

	# Free up any extra space
	rm -rf /root/.cache && \
	rm -rf /usr/share/sounds/alsa/*  && \
	pip uninstall -y setuptools && \
	apt-get remove --purge -y python-pip && \
	apt-get autoremove -y

COPY /src/*.mp3 /opt/
COPY credentials.json /root/.config/google-oauthlib-tool/
RUN echo "hi"
COPY /src/start.py /opt/


#CMD ["python", "/opt/start.py"]
CMD ["/bin/sh"]
