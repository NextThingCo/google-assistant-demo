# Base from Debian instead of Alpine, since Google uses glibc
FROM arm32v7/debian:stretch-slim
LABEL architecture="ARMv7"

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
WORKDIR /opt

# Install packages
RUN apt-get update && \
	apt-get install --no-install-recommends -y \
		alsa-utils \
		locales \
		rfkill \
		iproute \
		python-dev \
		python-dbus \
		python-eventlet \
		python-gobject \
		python-googleapi \
		python-psutil \
		python-pexpect \
		python-smbus \
		python-pip && \

	# Set locales
	locale-gen en_US en_US.UTF-8 && \
	sed -i -e "s/# $LANG.*/$LANG.UTF-8 UTF-8/" /etc/locale.gen && \
	dpkg-reconfigure --frontend=noninteractive locales && \
	update-locale LANG=$LANG && \

	pip install --upgrade pip setuptools && \
	pip install --no-cache-dir google-assistant-library && \
	pip install --no-cache-dir pyconnman PyDispatcher Flask Flask-SocketIO flask_uploads && \

	pip uninstall -y setuptools && \
	apt-get autoremove -y && \
	apt-get autoclean -y

COPY *.py /opt/
RUN ls /opt/ && python -m compileall /opt/. && ls /opt/
COPY resources /opt/resources
COPY webpage /opt/webpage
COPY configs/asoundrc /root/.asoundrc
COPY configs/limits.conf /etc/security/
COPY test.sh /opt/
COPY demo.py /opt/
ENV EXT_ANTENNA=1

#CMD ["/bin/sh"]
#CMD ["/usr/bin/python /opt/start.py"]
