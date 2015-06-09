##############################################################################
#
# Copyright 2015 KPMG N.V. (unless otherwise stated)
#
#   Licensed under the Apache License, Version 2.0 (the "License");
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
# This is the install snippet file, it does the work of installing ambari and is
# used in the dev install.sh command, and also catted into the packaged install script

#abort at first failure
set -e
set -o pipefail

yum install ambari-server -y
yum install -y pdsh wget curl
ambari-server setup -s

##########################################################
# By default enable two-way ssl between server and agents!
echo "security.server.two_way_ssl = true" >> /etc/ambari-server/conf/ambari.properties
##########################################################
# By default encrypt passwords stored in the database!
yum -y install expect
touch /tmp/tmp.mkey.temp
chmod 600 /tmp/tmp.mkey.temp
(< /dev/urandom tr -dc _A-Z-a-z-0-9 | head -c 32; date +%s | head -c 10; hostname) | sha256sum | base64 | head -c 32 > /tmp/tmp.mkey.temp
touch /tmp/tmp.mkeywrap.temp
chmod 600 /tmp/tmp.mkeywrap.temp
echo "spawn ambari-server setup-security" > /tmp/tmp.mkeywrap.temp
echo "expect \"Enter choice, (1-5): \"" >> /tmp/tmp.mkeywrap.temp
#4 is setup master encryption key
echo "send 4\\n;" >> /tmp/tmp.mkeywrap.temp
echo "expect \"locking the credential store: \"" >> /tmp/tmp.mkeywrap.temp
#Now input password
echo -n "send \"" >> /tmp/tmp.mkeywrap.temp
cat /tmp/tmp.mkey.temp | tr -d "\n" >> /tmp/tmp.mkeywrap.temp
echo "\\n\";" >> /tmp/tmp.mkeywrap.temp
echo "expect \"Re-enter master key: \"" >> /tmp/tmp.mkeywrap.temp
#Now input password
echo -n "send \"" >> /tmp/tmp.mkeywrap.temp
cat /tmp/tmp.mkey.temp | tr -d "\n" >> /tmp/tmp.mkeywrap.temp
echo "\\n\";" >> /tmp/tmp.mkeywrap.temp
echo "expect \"(y)? \"" >> /tmp/tmp.mkeywrap.temp
# yes to persisting the password
echo "send y\\n;" >> /tmp/tmp.mkeywrap.temp
expect /tmp/tmp.mkeywrap.temp
echo
rm /tmp/tmp.mkeywrap.temp
rm /tmp/tmp.mkey.temp
##########################################################
# end of install snippet file
##########################################################
