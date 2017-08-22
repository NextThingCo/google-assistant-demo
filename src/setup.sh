#!/bin/sh

DOCKERTAG=$(docker ps --format {{.Names}} | grep google-assistant)
echo $DOCKERTAG
