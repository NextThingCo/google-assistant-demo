# Base from Debian instead of Alpine, since Google uses glibc
FROM arm32v7/debian:stretch-slim
LABEL architecture="ARMv7"

WORKDIR /opt

# Install packages
RUN apt-get upgrade
RUN apt-get update
RUN apt-get install --no-install-recommends -y connman alsa-utils iproute

RUN apt-get install --no-install-recommends -y python-dev \
		python-dbus

RUN apt-get install --no-install-recommends -y 	python-psutil \
		python-pexpect \
		python-smbus \
		nano \
		python-pip

RUN pip install --upgrade pip setuptools && \
	pip install --no-cache-dir pyconnman

	#pip uninstall -y setuptools && \
	#apt-get autoremove -y && \
	#apt-get autoclean -y

COPY *.py /opt/
RUN python -m compileall /opt/.
RUN apt-get install --no-install-recommends -y python-cffi portaudio19-dev libffi-dev libssl-dev
RUN apt-get install --no-install-recommends -y python-dev build-essential
RUN python -m pip install google-assistant-sdk[samples]

#CMD ["/bin/sh"]
#CMD ["/usr/bin/python /opt/start.py"]
