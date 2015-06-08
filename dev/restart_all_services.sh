#! /bin/bash
##############################################################################
#
# Copyright 2015 KPMG N.V. (unless otherwise stated)
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
# Restart everything script, will restart the ambari server, restart all agents, wait for 70 seconds for a heartbeat, and then restart all components.
#

cluster=$1
ambari='localhost'
user='admin'
password='admin'

if [ -z "$1" ]; then
	echo "please state the name of the cluster to restart"
	exit 1
fi

echo "restarting ambari server"
ambari-server restart
sleep 10

#assumes deploy_from_blueprint was used...
echo "restarting all ambari agents"
pdsh -R ssh -g $cluster ambari-agent restart

echo "sleeping for 70 seconds (heartbeat duration)"
sleep 70


#find all service names
allnames=`curl -i -X GET --user $user:$password http://$ambari:8080/api/v1/clusters/$cluster/services/ -H "X-Requested-By:ambari" | grep "service_name" | awk -F '"' '{print $4}'`

echo "Stopping all services"
#stop them
for service in $allnames; do
	echo $service
	curl -i -X PUT -d '{"RequestInfo":{"context":"Stopping '$service'"},"Body":{"ServiceInfo":{"state":"INSTALLED"}}}' --user $user:$password http://$ambari:8080/api/v1/clusters/$cluster/services/$service -H "X-Requested-By:ambari"
done

echo "sleeping for 70 seconds (heartbeat duration)"
sleep 70

#Always start FreeIPA first if it is in the list
for service in $allnames; do
	if [ "$service" != "FREEIPA" ]; then
		continue
	fi
    echo "starting FreeIPA"
	echo $service
	curl -i -X PUT -d '{"RequestInfo":{"context":"Stopping '$service'"},"Body":{"ServiceInfo":{"state":"INSTALLED"}}}' --user $user:$password http://$ambari:8080/api/v1/clusters/$cluster/services/$service -H "X-Requested-By:ambari"
	echo "sleeping for 70 seconds (heartbeat duration)"
    sleep 70
done


#start everything
for service in $allnames; do
	echo $service
	curl -i -X PUT -d '{"RequestInfo":{"context":"Starting '$service'"},"Body":{"ServiceInfo":{"state":"STARTED"}}}' --user $user:$password http://$ambari:8080/api/v1/clusters/$cluster/services/$service -H "X-Requested-By:ambari"
done
echo "All request hrefs"
curl --user admin:admin http://localhost:8080/api/v1/clusters/default/requests | grep 'href' | grep "requests/" | awk -F '"' '{print $4}'
echo "Final request ID for automatic monitoring:"
curl --user admin:admin http://localhost:8080/api/v1/clusters/default/requests | grep "id" | tail -n 1 | awk -F ':' '{print $2}' | awk -F ' ' '{print $1}'
