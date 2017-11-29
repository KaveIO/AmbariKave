#!/bin/bash
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

TARGETFILE="sshhardened.conf"
INFOLINE="#KAVE ssh config hardening:"
SSHCONFIGOPTIONS="$INFOLINE
HostKey /etc/ssh/ssh_host_ed25519_key
HostKey /etc/ssh/ssh_host_rsa_key
HostKey /etc/ssh/ssh_host_ecdsa_key

KexAlgorithms curve25519-sha256@libssh.org,ecdh-sha2-nistp521,ecdh-sha2-nistp384,ecdh-sha2-nistp256,diffie-hellman-group-exchange-sha256

Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com,aes256-ctr,aes192-ctr,aes128-ctr

MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com,umac-128-etm@openssh.com,hmac-sha2-512,hmac-sha2-256,umac-128@openssh.com

AuthenticationMethods publickey

LogLevel VERBOSE

Subsystem sftp  /usr/lib/ssh/sftp-server -f AUTHPRIV -l INFO
PermitRootLogin No
UsePrivilegeSeparation sandbox"

if [[ -z $(grep "$INFOLINE" "$TARGETFILE") ]]; then echo "$SSHCONFIGOPTIONS" >> "$TARGETFILE"; fi

#Deactivate short moduli:
awk '$5 >= 3071' /etc/ssh/moduli > /etc/ssh/moduli.tmp && mv /etc/ssh/moduli.tmp /etc/ssh/moduli