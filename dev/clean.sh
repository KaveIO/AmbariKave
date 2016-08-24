#! /bin/bash
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
#
# Script to completely clean an ambari installation
# only cleans ambari itself, does nothing with the services that
# ambari may have installed. Accepts one arguement, the name of the pdsh group
# associated to the whole cluster, if supplied will use pdsh to remove agents
# from all the machines in the cluster as well as the local machine
#

echo "This will completely destroy your local ambari installation and database."
read -p "Are you sure? " -n 1 -r
echo    # (optional) move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "OK, sleeping 5 secs in case you change your mind"
    sleep 5
else
	echo "Thank goodness, exiting"
	exit 0
fi


cluster=$1

clustercmd=""

if [ ! -z "$1" ]; then

	if ! type pdsh >/dev/null 2>/dev/null ; then
		echo 'no pdsh installed'
		exit 1
	fi

	pdsh_version=`pdsh -V | head -n 1 | awk '{print $1}' | awk -F '-' '{print $2}'`
	pdsh_groups=`pdsh -h 2>&1 | tail -n 10 | grep groupname`

	if [[  ${pdsh_version} < "2.27" ]]; then
	        echo "pdsh version >= 2.27 needed for this script, you have"
	        pdsh -V
	        exit 1
	fi

	if [[  ${pdsh_groups} == *"-g groupname"* ]]; then
	        true
	else
	        pdsh -h
	        echo "No pdsh groups detected, install newer version or install pdsh-mod-dshgroup"
	        exit 1
	fi

	if [ ! -e ~/.dsh/group/$1 ]; then
		echo "no dsh group called "$1" found, did you type the cluster name in wrongly?"
		echo "deploy_from_blueprint makes groups named after the cluster, if you didn't use that this won't work either"
		echo "you can also make the groups yourself, with all nodes"
		exit 1
	fi

	clustercmd="pdsh -g $cluster "

fi


ambari-server stop
${clustercmd}ambari-agent stop
sleep 5
yum -y erase ambari-server
${clustercmd}yum -y erase ambari-agent
su - postgres bash -c 'psql -c "drop role ambari"; psql -c "drop database ambari"; psql -c "drop database ambarirca";'
rm -f .pgpass
rm -rf /var/lib/ambari-server/*
rm -rf /etc/ambari-server/*
${clustercmd}rm -rf /var/lib/ambari-agent/*
${clustercmd}rm -rf /etc/ambari-agent/*
${clustercmd}rm -rf /etc/yum.repos.d/ambari.repo
