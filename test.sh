#!/bin/sh

echo 49 > /sys/class/gpio/export
echo "out" > /sys/class/gpio/gpio49/direction
echo 1 > /sys/class/gpio/gpio49/value

docker run --privileged --net=host --cap-add=NET_ADMIN --cap-add SYS_RAWIO --device /dev/mem -v /sys:/sys -v /var/run/dbus:/var/run/dbus -v /data/var/lib/connman:/var/lib/connman -v /data/test:/opt -it google
