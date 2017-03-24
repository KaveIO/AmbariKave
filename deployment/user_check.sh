#!/bin/bash
# Copyright 2016 KPMG Advisory N.V. (unless otherwise stated)
# "http://www.apache.org/licenses/LICENSE-2.0"
# init
USERID="$1"

/bin/egrep  -i "^${USERID}:" /etc/passwd
#awk -F':' '/^{USERID}/{print $1}' /etc/passwd
if [ $? -eq 0 ]; then
   echo "-1"
else
   echo "0"
fi
