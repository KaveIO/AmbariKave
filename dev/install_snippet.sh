##############################################################################
#
# Copyright 2016 KPMG Advisory N.V. (unless otherwise stated)
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
yum info epel-release 2>/dev/null | grep installed
epel_not_installed=$?
set -e
#set -o pipefail #not a good idea, causes failures even in actual successful situations

os=`uname -r`
flavor='centos'
if [[ "$os" == *"el7"* ]]; then
	os="centos7"
	if [ -e "/etc/redhat-release" ]; then
		release=`cat /etc/redhat-release`
		if [[ "$release" == *" 7."* ]]; then
			if [[ "$release" == "Red Hat"* ]]; then
				flavor="redhat"
			fi
		fi
	fi
else
	echo "This script is not tested/ready for this operating system"
fi

yum install -y wget curl
wget http://public-repo-1.hortonworks.com/ambari/${os}/2.x/updates/2.6.2.0/ambari.repo -O ambari.repo
cp ambari.repo /etc/yum.repos.d/
# conflicts with HDP utils and pre-installed pdsh version on centos6, need HDP repo file


yum install ambari-server -y
ambari-server setup -s

# install requests library for python
if [[ "$flavor" == "centos" ]]; then
	yum install -y epel-release
else
	if [[ $epel_not_installed -ne 0 ]]; then
		wget https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
		yum -y install epel-release-latest-7.noarch.rpm
	fi
fi
# necessary step to update epel and HDP cached repos
yum clean all
yum install -y pdsh python-devel python-pip
pip install requests
pip install --upgrade requests

if [[ "$os" == *"7" ]]; then
	yum install -y pdsh-mod-dshgroup
	wget http://download.opensuse.org/repositories/shells:fish:release:2/CentOS_7/shells:fish:release:2.repo
	yum -y install fish
fi

encrypt_number="4"

version=`ambari-server --version`

if [[ "$version" == "2.1."* ]]; then
	encrypt_number="2"
elif [[ "$version" == "2.2."* ]]; then
	encrypt_number="2"
elif [[ "$version" == "1.7."* ]]; then
	encrypt_number="4"
elif [[ "$version" == "2.4."* ]]; then
	encrypt_number="2"
elif [[ "$version" == "2.5."* ]]; then
	encrypt_number="2"
elif [[ "$version" == "2.6."* ]]; then
	encrypt_number="2"
else
	echo "This script is not tested/ready for this version of Ambari"
	exit 1
fi

##########################################################
# By default enable two-way ssl between server and agents!
echo "security.server.two_way_ssl = true" >> /etc/ambari-server/conf/ambari.properties
# Increase timeouts for agent jobs
sed -i -e 's/agent.stack.retry.tries=5/agent.stack.retry.tries=20/g' /etc/ambari-server/conf/ambari.properties
sed -i -e 's/agent.task.timeout=900/agent.task.timeout=3600/g' /etc/ambari-server/conf/ambari.properties
# Install MySQL-connector and link it to be available for agent nodes
yum install mysql-connector-java* -y && cd /var/lib/ambari-server/resources/ && ln -s /usr/share/java/mysql-connector-java.jar mysql-connector-java.jar
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
echo "send $encrypt_number\\n;" >> /tmp/tmp.mkeywrap.temp
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
# By default change the ambari database password!
temppw=`(< /dev/urandom tr -dc _A-Z-a-z-0-9 | head -c 32; date +%s | head -c 10; hostname) | sha256sum | base64 | head -c 32`
if [ -e ~/.pgpass ]; then
	mv ~/.pgpass ~/.pgpass_blacp
fi
echo -ne "*:*:ambari:ambari:" > ~/.pgpass; cat /etc/ambari-server/conf/password.dat >> ~/.pgpass; chmod 0600 ~/.pgpass
psql -U ambari ambari -c "ALTER USER ambari WITH PASSWORD '$temppw';" ; echo $temppw > /etc/ambari-server/conf/password.dat
chmod 0600 /etc/ambari-server/conf/password.dat
rm -f ~/.pgpass
if [ -e ~/.pgpass_blacp ]; then
	mv ~/.pgpass_blacp ~/.pgpass
fi

##########################################################
# end of install snippet file
##########################################################
