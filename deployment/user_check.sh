#!/bin/bash
# init
USERID="$1"

/bin/egrep  -i "^${USERID}:" /etc/passwd
#awk -F':' '/^{USERID}/{print $1}' /etc/passwd
if [ $? -eq 0 ]; then
   echo "-1"
else
   echo "0"
fi
