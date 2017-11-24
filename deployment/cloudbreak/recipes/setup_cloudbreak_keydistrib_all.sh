#!/bin/sh
##############################################################################
#
# Copyright 2017 KPMG Advisory N.V. (unless otherwise stated)
#
# Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
##############################################################################

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
