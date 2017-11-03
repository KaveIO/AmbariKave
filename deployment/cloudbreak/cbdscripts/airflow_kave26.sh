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
credential select --name rallycred
blueprint select --name airflow26
instancegroup configure --AZURE --instanceGroup admin --nodecount 1 --ambariServer true --templateName d2v2-azure --securityGroupName default-azure-only-ssh-and-ssl
instancegroup configure --AZURE --instanceGroup airflow --nodecount 1 --ambariServer false --templateName a2v2-azure --securityGroupName default-azure-only-ssh-and-ssl
network select --name default-azure-network
stack create --AZURE --name airflow26-shelltest --region "North Europe"
hostgroup configure --hostgroup admin --recipeNames "preallhosts,patchambari33systemd"
hostgroup configure --hostgroup airflow --recipeNames "preallhosts"
cluster create --ambariVersion "2.5.1.0" --ambariRepoBaseURL "http://public-repo-1.hortonworks.com/ambari/centos7/2.x/updates/2.5.1.0" --ambariRepoGpgKey "http://public-repo-1.hortonworks.com/ambari/centos7/2.x/updates/2.5.1.0/RPM-GPG-KEY/RPM-GPG-KEY-Jenkins" --stack "HDP" --version "2.6.1" --stackRepoId "HDP-2.6" --stackBaseURL "http://public-repo-1.hortonworks.com/HDP/centos7/2.x/updates/2.6.1.0" --utilsRepoId "HDP-UTILS-1.1.0.21" --utilsBaseURL "http://public-repo-1.hortonworks.com/HDP-UTILS-1.1.0.21/repos/centos7" --verify true
