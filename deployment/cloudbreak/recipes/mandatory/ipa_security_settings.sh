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

#A POST recipe to be executed on the Ambari Node
ambari_user="admin"
ambari_password="admin"
ambari_port=8080
ambari_host="localhost"
#Get clustername
cluster_name="$(curl -u ${ambari_user}:${ambari_password} -i -H 'X-Requested-By: ambari'  \
  http://$ambari_host:$ambari_port/api/v1/clusters 2>/dev/null | sed -n 's/.*"cluster_name" : "\([^\"]*\)".*/\1/p')"

ambari_api_url="http://$ambari_host:$ambari_port/api/v1/clusters/$cluster_name"

#Get host on which FreeIPA server is installed:
eval freeipa_host="$(curl -u ${ambari_user}:${ambari_password} -i -H 'X-Requested-By: ambari'  \
  $ambari_api_url/services/FREEIPA/components/FREEIPA_SERVER?fields=host_components/HostRoles/host_name \
  2>/dev/null | grep "\"host_name\"" | awk '{print $3}')"
#--------------------------------------------------------------------------------------------------------------
#Actual IPA policy and security setting modifications start below

#Change the password policy
salt $freeipa_host cmd.run 'cat /root/admin-password | kinit admin && ipa pwpolicy-mod --minclasses=4 --minlength=20'

#Get hosts on which Kavetoolbox Gate is installed:
gateway_nodes="$(curl -u ${ambari_user}:${ambari_password} -i -H 'X-Requested-By: ambari'  \
  $ambari_api_url/services/KAVETOOLBOX/components/KAVETOOLBOXGATE?fields=host_components/HostRoles/host_name \
  2>/dev/null | grep '"host_name' | awk '{print $3}' | tr -d \")"

#Enable user home directories automatic creation
salt $freeipa_host cmd.run 'authconfig --enablemkhomedir --update'


#Create the HBAC allow_all rule for admins:
salt $freeipa_host cmd.run "ipa hbacrule-add admins_allow_all \
--desc='A rule granting access to all nodes for the admins group' --hostcat='all' --servicecat='all'"

#Add "admins" group to the new rule:
salt $freeipa_host cmd.run "ipa hbacrule-add-user --groups='admins' admins_allow_all"

#Add "cloudbreak" system user to FreeIPA
salt $freeipa_host cmd.run "ipa user-add 'cloudbreak' \
--first='cloudbreak' --last='System account' --uid=`id -u cloudbreak`"

#Disable allow_all HBAC rule
salt $freeipa_host cmd.run 'ipa hbacrule-disable allow_all'