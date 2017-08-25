# Base from Debian instead of Alpine, since Google uses glibc
FROM arm32v7/debian:stretch-slim
LABEL architecture="ARMv7"

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
COPY ntc-google-assistant /opt/
COPY asoundrc /root/.asoundrc

# Install packages
RUN apt-get update && \
	apt-get install --no-install-recommends -y \
		portaudio19-dev bash

COPY credentials.json /root/.config/google-oauthlib-tool/
WORKDIR /opt


ENTRYPOINT /bin/bash
