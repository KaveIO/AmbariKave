#!/bin/bash
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


# fetch secret files from freeipa node and distribute them to all the rest in the cluster
for filename in $list_of_secret_files
do
    echo `salt $freeipa_host cmd.run 'cat $filename' --out txt | awk '{print $2}'` > $filename
    salt-cp '*' $filename $filename
done

#Add component to the hosts
for node in $hostlist
do
curl -i -H "X-Requested-By: ambari" -u ${ambari_user}:${ambari_password} -X POST "http://$ambari_host:$ambari_port/api/v1/clusters/$cluster_name/hosts/$node/host_components/FREEIPA_CLIENT"
curl -i -H "X-Requested-By: ambari" -u ${ambari_user}:${ambari_password} -X PUT -d '{"HostRoles": {"state": "INSTALLED"}}' "http://$ambari_host:$ambari_port/api/v1/clusters/$cluster_name/hosts/$node/host_components/FREEIPA_CLIENT"
done