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
cluster_name="$(curl -u ${ambari_user}:${ambari_password} -i -H 'X-Requested-By: ambari'  http://$ambari_host:$ambari_port/api/v1/clusters 2>/dev/null | sed -n 's/.*"cluster_name" : "\([^\"]*\)".*/\1/p')"

#Get all hosts from ambari API
hostlist=`curl -i -H "X-Requested-By: ambari" -u ${ambari_user}:${ambari_password} -X GET http://localhost:8080/api/v1/hosts 2>/dev/null | grep "host_name" | awk '{print $3}' | tr -d \"`

#Get host on which FreeIPA server is installed:
eval freeipa_host="$(curl -u ${ambari_user}:${ambari_password} -i -H 'X-Requested-By: ambari'  http://$ambari_host:$ambari_port/api/v1/clusters/$cluster_name/services/FREEIPA/components/FREEIPA_SERVER?fields=host_components/HostRoles/host_name 2>/dev/null | grep "\"host_name\"" | awk '{print $3}')"

# fetch secret files from freeipa node, distribute them to all the rest.
for filename in $list_of_secret_files
do
    echo `salt $freeipa_host cmd.run "cat $filename" --out txt | awk '{print $2}'` > $filename
    chmod 600 $filename
        for current_host in $hostlist
    do
        if [ "$current_host" != "$freeipa_host" ]
        then
        salt-cp $current_host $filename $filename
        fi
    done
done

#Use Ambari API to install FREEIPA_CLIENT component on all nodes except FreeIPA_Server
for current_host in $hostlist
do
        if [ "$current_host" != "$freeipa_host" ]
        then
        curl -i -H "X-Requested-By: ambari" -u ${ambari_user}:${ambari_password} -X POST "http://$ambari_host:$ambari_port/api/v1/clusters/$cluster_name/hosts/$current_host/host_components/FREEIPA_CLIENT"
        sleep 10
        curl -i -H "X-Requested-By: ambari" -u ${ambari_user}:${ambari_password} -X PUT -d '{"HostRoles": {"state": "INSTALLED"}}' "http://$ambari_host:$ambari_port/api/v1/clusters/$cluster_name/hosts/$current_host/host_components/FREEIPA_CLIENT"
        fi
done
