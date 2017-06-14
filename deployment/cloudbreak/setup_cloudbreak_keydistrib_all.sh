#!/bin/sh

#This is a Cloudbreak pre-recipe for all nodes.

#Make sure you insert the desired private key below and that you replace that with a new one on every host when the deployment is finished.
USER=cloudbreak
KEYFILE=/home/$USER/.ssh/id_rsa
cat << EOF > $KEYFILE
-----BEGIN RSA PRIVATE KEY-----
C353D87F87DFG87FG7DF7G96FD768G78FDG67SF67GSF
KEYCONTENT
ADSADFSDAFSADFSAFRV35655V45C35C13C5234C
-----END RSA PRIVATE KEY-----
EOF
chown $USER:$USER $KEYFILE
chmod 600 $KEYFILE
