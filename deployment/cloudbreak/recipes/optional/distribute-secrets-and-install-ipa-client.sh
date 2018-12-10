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

ambari_user="admin"
ambari_password="admin"
ambari_port=8080
ambari_host="localhost"

list_of_secret_files="/root/admin-password
/root/robot-admin-password
/root/someadmin-password"


#Get clustername
cluster_name="$(curl -u ${ambari_user}:${ambari_password} -i \
  -H 'X-Requested-By: ambari'  http://$ambari_host:$ambari_port/api/v1/clusters \
  2>/dev/null | sed -n 's/.*"cluster_name" : "\([^\"]*\)".*/\1/p')"

ambari_api_url="http://$ambari_host:$ambari_port/api/v1/clusters/$cluster_name"

#Get host on which FreeIPA server is installed:
eval freeipa_host="$(curl -u ${ambari_user}:${ambari_password} -i -H 'X-Requested-By: ambari'  \
  $ambari_api_url/services/FREEIPA/components/FREEIPA_SERVER?fields=host_components/HostRoles/host_name \
  2>/dev/null | grep "\"host_name\"" | awk '{print $3}')"

#Get all hosts, except FreeIPA server, from ambari API
nonipa_hosts=`curl -i -H "X-Requested-By: ambari" \
  -u ${ambari_user}:${ambari_password} -X GET http://$ambari_host:$ambari_port/api/v1/hosts \
  | grep host_name| sed -n 's/.*"host_name" : "\([^\"]*\)".*/\1/p' | grep -v $freeipa_host`


# fetch secret files from freeipa node, distribute them to all the rest.
for filename in $list_of_secret_files
do
    echo `salt $freeipa_host cmd.run "cat $filename" --out txt | awk '{print $2}'` > $filename
    chmod 600 $filename
        for current_host in $nonipa_hosts
    do
        salt-cp $current_host $filename $filename
    done
done

##prepare csv list of hosts with freeipa server host excluded
#host_csv=""
#for current_host in $hostlist
#   do
#        if [ "$current_host" != "$freeipa_host" ]
#        then
#        host_csv=$current_host","$host_csv
#        fi
#   done
#host_csv=$(sed 's/,\s*$//' <<< $host_csv)

current_host=""
for current_host in $nonipa_hosts; 
   do
		curl -u ${ambari_user}:${ambari_password} -H "X-Requested-By:ambari" -i -X POST -d \
		'{"RequestInfo":{"context":"Install FreeIPA Client"},"Body":{"host_components":[{"HostRoles":{"component_name":"FREEIPA_CLIENT"}}]}}' \
		$ambari_api_url/hosts?Hosts/host_name=$current_host;
		sleep 3
   done
   
current_host=""
for current_host in $nonipa_hosts; 
   do
		curl -u ${ambari_user}:${ambari_password} -H "X-Requested-By:ambari" -i -X PUT -d \
		'{"RequestInfo":{"context":"Install FREEIPA Client",
						 "operation_level":{"level":"HOST_COMPONENT","cluster_name":"'$cluster_name'","host_name":"'$current_host'"}},
						 "Body":{"HostRoles":{"state":"INSTALLED"}}}' \
		$ambari_api_url/hosts/$current_host/host_components/FREEIPA_CLIENT?HostRoles/state=INIT
		sleep 5
   done   


##Use Ambari API to install FREEIPA_CLIENT component on all nodes except FreeIPA_Server
#post_data="{
#  \"RequestInfo\":{
#    \"query\":\"Hosts/host_name.in($host_csv)\",
#    \"context\":\"Install Clients.\"
#  },
#  \"Body\":{
#    \"host_components\":[
#    {
#      \"HostRoles\":{
#        \"component_name\":\"FREEIPA_CLIENT\"
#      }
#    }
#    ]
#  }
#}"

##trying additional delay to avoid race confitions
#sleep 120
#
##Add FREEIPA_CLIENT component to all hosts except FreeIPA server
#curl -i -H "X-Requested-By: ambari" -u ${ambari_user}:${ambari_password} \
#  -X POST -d "$post_data" "$ambari_api_url/hosts"
#  
##Tell Amari to install the newly added component(s)  
#curl -i -H "X-Requested-By: ambari" -u ${ambari_user}:${ambari_password} \
#  -X PUT -d '{ "HostRoles": { "state":"INSTALLED" } }' "$ambari_api_url/host_components?HostRoles/state=INIT"
