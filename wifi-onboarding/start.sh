#!/bin/sh

echo -n "starting dnsmasq..."
! dnsmasq && echo "ERROR" && exit 1
echo "OK"

echo -n "setup default route and port redirection..."
! iptables -t nat -I PREROUTING 1 -i wlan0 -p tcp --dport 80 -j DNAT --to-destination 192.168.84.1:8080 && echo "ERROR" && exit 1
echo "OK"

cd /APP

echo "run wifi-onboarding..."
/APP/wifi-onboarding
