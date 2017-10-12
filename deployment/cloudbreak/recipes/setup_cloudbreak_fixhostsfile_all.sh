#!/bin/sh

#This is a Cloudbreak pre-recipe for every host.

#Replace to avoid some weird behavior - my >> did not get respected.
arp -a | awk '{ gsub("\\(|)","", $2); split($1, arr, "."); print $2"\t"$1" "arr[1]}' | (echo -e "`ifconfig eth0 | grep 'inet' | cut -d: -f2 | awk '{print $2}'`\t`hostname -f` `hostname -s`" && cat) | (echo -e "::1\t\tlocalhost localhost.localdomain localhost6 localhost6.localdomain6" && cat) | (echo -e "127.0.0.1\tlocalhost localhost.localdomain localhost4 localhost4.localdomain4" && cat) > /etc/hosts
