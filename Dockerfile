# Base from Debian instead of Alpine, since Google uses glibc
FROM arm32v7/debian:stretch-slim
LABEL architecture="ARMv7"

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
WORKDIR /opt

# Install packages
RUN apt-get update && \
	apt-get install --no-install-recommends -y \
		connman \
		alsa-utils \
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

	pip install --upgrade pip setuptools && \
	pip install --no-cache-dir google-assistant-library && \
	pip install --no-cache-dir pyconnman PyDispatcher Flask Flask-SocketIO flask_uploads && \

	pip uninstall -y setuptools && \
	apt-get autoremove -y && \
	apt-get autoclean -y && \

	rm /var/lib/apt/lists/deb.debian.org_debian_dists_stretch_main_binary-armhf_Packages.lz4

COPY *.py /opt/
RUN python -m compileall /opt/.
COPY resources /opt/resources
COPY webpage /opt/webpage
COPY configs/asoundrc /root/.asoundrc
COPY configs/limits.conf /etc/security/

#CMD ["/usr/bin/python /opt/start.py"]
