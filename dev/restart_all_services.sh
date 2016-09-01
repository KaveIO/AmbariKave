#! /bin/bash
##############################################################################
#
# Copyright 2016 KPMG Advisory N.V. (unless otherwise stated)
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

#
# Restart everything script, will restart the ambari server, restart all agents,
# wait for 70 seconds for a heartbeat, and then restart all components.
# First argument is the name fo the cluster to restart
# second argument is the name of a local netrc file to authenticate
#

cluster=$1
ambari='localhost'

if [ -z "$1" ]; then
	echo "please state the name of the cluster to restart"
	exit 1
fi

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
	echo "you can also make the groups yourself, with all ambari nodes"
	exit 1
fi


if [ ! -f "$HOME/.netrc" ]; then
	echo "You must supply a .netrc file with the credentials to connect"
	echo "to ambari. The file $HOME/netrc does not exist or is unreadable"
	exit 1
fi

echo "restarting ambari server"
ambari-server restart
sleep 10

#assumes deploy_from_blueprint was used...
echo "restarting all ambari agents"
pdsh -R ssh -g $cluster ambari-agent stop 2>/dev/null
sleep 15
pdsh -R ssh -g $cluster ambari-agent start 2>/dev/null
if [[ $? -ne 0 ]]; then
	echo "retry agent start"
	sleep 15
	pdsh -R ssh -g $cluster ambari-agent start 2>/dev/null
fi


echo "sleeping for 70 seconds (heartbeat duration)"
sleep 70
op=`pdsh -R ssh -g $cluster ambari-agent status 2>/dev/null | grep "not running"`
if [ ! -z "$op" ]; then
	echo "Warning, at least one ambari agent is still not started, check the log files for that node: /var/log/ambari-agent/ambari-agent.log"
	echo "$op"
	sleep 10
fi

#find all service names
allnames=`curl --retry 5  -i -X GET --netrc http://$ambari:8080/api/v1/clusters/$cluster/services/ -H "X-Requested-By:ambari" | grep "service_name" | awk -F '"' '{print $4}'`

echo "Restarting FreeIPA first, if it exists"
#stop them
if [[ "$allnames" == *"FREEIPA"* ]]; then
	service="FREEIPA"
	echo $service
	curl --retry 5  -i -X PUT -d '{"RequestInfo":{"context":"Stopping '$service'"},"Body":{"ServiceInfo":{"state":"INSTALLED"}}}' --netrc http://$ambari:8080/api/v1/clusters/$cluster/services/$service -H "X-Requested-By:ambari"
	echo "sleeping for 70 seconds, (heartbeat duration)"
	sleep 30
	# manual start to ensure the correct ordering
	pdsh -R ssh -g $cluster service ipa start
	sleep 40
	curl --retry 5  -i -X PUT -d '{"RequestInfo":{"context":"Starting '$service'"},"Body":{"ServiceInfo":{"state":"STARTED"}}}' --netrc http://$ambari:8080/api/v1/clusters/$cluster/services/$service -H "X-Requested-By:ambari"
	echo "sleeping for 70 seconds (heartbeat duration)"
	sleep 70
	# end with manual start in case the stop/install takes too long.
	service ipa start
fi

echo "Stopping all services"
#stop them
for service in $allnames; do
	if [ "$service" == "FREEIPA" ]; then
		continue
	fi
	echo "stopping" $service
	curl --retry 5  -i -X PUT -d '{"RequestInfo":{"context":"Stopping '$service'"},"Body":{"ServiceInfo":{"state":"INSTALLED"}}}' --netrc http://$ambari:8080/api/v1/clusters/$cluster/services/$service -H "X-Requested-By:ambari"
done

echo "sleeping for 70 seconds (heartbeat duration)"
sleep 70

for service in $allnames; do
	if [ "$service" == "FREEIPA" ]; then
		continue
	fi
    echo "starting" $service
	curl --retry 5  -i -X PUT -d '{"RequestInfo":{"context":"Starting '$service'"},"Body":{"ServiceInfo":{"state":"STARTED"}}}' --netrc http://$ambari:8080/api/v1/clusters/$cluster/services/$service -H "X-Requested-By:ambari"
done


echo "All request hrefs"
curl --retry 5  --netrc http://$ambari:8080/api/v1/clusters/$cluster/requests 2>/dev/null | grep 'href' | grep "requests/" | awk -F '"' '{print $4}'
echo "Final request ID for semi-automatic monitoring:"
curl --retry 5  --netrc http://$ambari:8080/api/v1/clusters/$cluster/requests 2>/dev/null | grep "id" | tail -n 1 | awk -F ':' '{print $2}' | awk -F ' ' '{print $1}'
