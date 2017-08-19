# Base from Debian instead of Alpine, since Google uses glibc
FROM arm32v7/debian:stretch-slim
LABEL architecture="ARMv7"

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

COPY client.json /opt/
COPY src/asoundrc /root/.asoundrc

# Install packages
RUN apt-get update && \

	apt-get install --no-install-recommends -y \
		alsa-utils \
		locales \
		connman \
		python3-dev \
		python3-venv

# Set locales
RUN locale-gen en_US en_US.UTF-8 && \
	sed -i -e "s/# $LANG.*/$LANG.UTF-8 UTF-8/" /etc/locale.gen && \
	dpkg-reconfigure --frontend=noninteractive locales && \
	update-locale LANG=$LANG

# Setup python virtual enviornment
RUN python3 -m venv env && \
	env/bin/python -m pip install --upgrade pip setuptools

# Start python virtual enviornment and install Google SDK
RUN  . env/bin/activate && \
	python -m pip install --upgrade google-assistant-library && \
	python -m pip install --upgrade google-auth-oauthlib[tool]

COPY /src/start.py /opt/

ENTRYPOINT . env/bin/activate && env/bin/python /opt/start.py
#ENTRYPOINT . env/bin/activate && /bin/sh
