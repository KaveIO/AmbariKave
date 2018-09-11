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
cluster_name () {
    echo "$(curl -u ${ambari_user}:${ambari_password} -i \
      -H 'X-Requested-By: ambari'  http://$ambari_host:$ambari_port/api/v1/clusters \
      2>/dev/null | sed -n 's/.*"cluster_name" : "\([^\"]*\)".*/\1/p')"
}

#Get all hosts from ambari API
hostlist () {
    echo "$(curl -i -H "X-Requested-By: ambari" \
      -u ${ambari_user}:${ambari_password} -X GET http://$ambari_host:$ambari_port/api/v1/hosts \
    2>/dev/null | grep "host_name" | awk '{print $3}' | tr -d \")"
}

ambari_api_url () { 
	echo http://$ambari_host:$ambari_port/api/v1/clusters/$(cluster_name) 
}

#Get host on which FreeIPA server is installed:
freeipa_host () {
    echo $(curl -u ${ambari_user}:${ambari_password} -i -H 'X-Requested-By: ambari'  \
      $(ambari_api_url)/services/FREEIPA/components/FREEIPA_SERVER?fields=host_components/HostRoles/host_name \
    2>/dev/null | grep "\"host_name\"" | awk '{print $3}' | tr -d \")
}

# fetch secret files from freeipa node, distribute them to all the rest.
function fetch_secret_files {
    for filename in $list_of_secret_files
    do
    	until salt $(freeipa_host) cmd.run "ls $filename"; do echo sleep 60; done
        echo `salt $(freeipa_host) cmd.run "cat $filename" --out txt | awk '{print $2}'` > $filename
        chmod 600 $filename
        for current_host in $(hostlist)
        do
            if [ "$current_host" != "$(freeipa_host)" ]
            then
                salt-cp $current_host $filename $filename
            fi
        done
    done
}

#prepare csv list of hosts with freeipa server host excluded
host_csv=""
for current_host in $(hostlist)
   do
        if [ "$current_host" != "$(freeipa_host)" ]
        then
        host_csv=$current_host","$host_csv
        fi
   done
host_csv=$(sed 's/,\s*$//' <<< $host_csv)


#Use Ambari API to install FREEIPA_CLIENT component on all nodes except FreeIPA_Server
post_data="{
  \"RequestInfo\":{
    \"query\":\"Hosts/host_name.in($host_csv)\",
    \"context\":\"Install Clients.\"
  },
  \"Body\":{
    \"host_components\":[
    {
      \"HostRoles\":{
        \"component_name\":\"FREEIPA_CLIENT\"
      }
    }
    ]
  }
}"

#Add FREEIPA_CLIENT component to all hosts except FreeIPA server
function add_freeipa_client {
    curl -i -H "X-Requested-By: ambari" -u ${ambari_user}:${ambari_password} \
     -X POST -d "$post_data" "$(ambari_api_url)/hosts"
}
  
#Tell Amari to install the newly added component(s)  
function install_freeipa_client {
    curl -i -H "X-Requested-By: ambari" -u ${ambari_user}:${ambari_password} \
     -X PUT -d '{ "HostRoles": { "state":"INSTALLED" } }' "$(ambari_api_url)/host_components?HostRoles/state=INIT"
}

function main {
    fetch_secret_files
    add_freeipa_client
    install_freeipa_client
}

main &