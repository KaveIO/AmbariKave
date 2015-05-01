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
from resource_management import *
from resource_management.core.system import System
import os

config = Script.get_config()

hostname = config["hostname"]

############## Copied from knox configuration!! #######################
namenode_hosts = default("/clusterHostInfo/namenode_host", None)
if type(namenode_hosts) is list:
    namenode_host = namenode_hosts[0]
else:
    namenode_host = namenode_hosts

has_namenode = (namenode_host is not None)
namenode_http_port = "50070"
namenode_rpc_port = "8020"

if has_namenode:
    if 'dfs.namenode.http-address' in config['configurations']['hdfs-site']:
        namenode_http_port = get_port_from_url(config['configurations']['hdfs-site']['dfs.namenode.http-address'])
    if 'dfs.namenode.rpc-address' in config['configurations']['hdfs-site']:
        namenode_rpc_port = get_port_from_url(config['configurations']['hdfs-site']['dfs.namenode.rpc-address'])

rm_hosts = default("/clusterHostInfo/rm_host", None)
if type(rm_hosts) is list:
    rm_host = rm_hosts[0]
else:
    rm_host = rm_hosts
has_rm = (rm_host is not None)

jt_rpc_port = "8050"
rm_port = "8080"

if has_rm:
    if 'yarn.resourcemanager.address' in config['configurations']['yarn-site']:
        jt_rpc_port = get_port_from_url(config['configurations']['yarn-site']['yarn.resourcemanager.address'])

    if 'yarn.resourcemanager.webapp.address' in config['configurations']['yarn-site']:
        rm_port = get_port_from_url(config['configurations']['yarn-site']['yarn.resourcemanager.webapp.address'])

hive_http_port = default('/configurations/hive-site/hive.server2.thrift.http.port', "10001")
hive_port = default('/configurations/hive-site/hive.server2.thrift.http.port', "10000")
hive_http_path = default('/configurations/hive-site/hive.server2.thrift.http.path', "cliservice")
hive_server_hosts = default("/clusterHostInfo/hive_server_host", None)
if type(hive_server_hosts) is list:
    hive_server_host = hive_server_hosts[0]
else:
    hive_server_host = hive_server_hosts

templeton_port = default('/configurations/webhcat-site/templeton.port', "50111")
webhcat_server_hosts = default("/clusterHostInfo/webhcat_server_host", None)
if type(webhcat_server_hosts) is list:
    webhcat_server_host = webhcat_server_hosts[0]
else:
    webhcat_server_host = webhcat_server_hosts

hbase_master_port = default('/configurations/hbase-site/hbase.rest.port', "8080")
hbase_master_hosts = default("/clusterHostInfo/hbase_master_hosts", None)
if type(hbase_master_hosts) is list:
    hbase_master_host = hbase_master_hosts[0]
else:
    hbase_master_host = hbase_master_hosts

oozie_server_hosts = default("/clusterHostInfo/oozie_server", None)
if type(oozie_server_hosts) is list:
    oozie_server_host = oozie_server_hosts[0]
else:
    oozie_server_host = oozie_server_hosts

has_oozie = (oozie_server_host is not None)
oozie_server_port = "11000"

if has_oozie:
    if 'oozie.base.url' in config['configurations']['oozie-site']:
        oozie_server_port = get_port_from_url(config['configurations']['oozie-site']['oozie.base.url'])

history_hosts = default("/clusterHostInfo/hs_host", None)
if type(history_hosts) is list:
    history_host = history_hosts[0]
else:
    history_host = history_hosts

has_hs = (history_host is not None)

######################################################################################


namenode = namenode_host
if namenode is None or namenode == "":
    namenode = 'localhost'
    #can reconfigure later?

yarn_host = rm_host
if yarn_host is None or yarn_host == "":
    yarn_host = 'localhost'
    #can reconfigure later?

yarn_host = rm_host
if yarn_host is None or yarn_host == "":
    yarn_host = 'localhost'
    #can reconfigure later?

oozie_host = oozie_server_host
if oozie_host is None or oozie_host == "":
    oozie_host = 'localhost'
    #can reconfigure later?

hcat_host = webhcat_server_host
if hcat_host is None or hcat_host == "":
    hcat_host = 'localhost'
    #can reconfigure later?

hive_host = hive_server_host
if hive_host is None or hive_host == "":
    hive_host = 'localhost'
    #can reconfigure later?

history_host = history_host
if history_host is None or history_host == "":
    history_host = 'localhost'
    #can reconfigure later?

############## PORTS #######################


web_ui_port = default('configurations/hue/web_ui_port', '8000')
web_ui_host = default('configurations/hue/web_ui_host', '0.0.0.0')
yarn_api_port = default('configurations/hue/yarn_api_port', '8088')
nodemanager_port = default('configurations/hue/nodemanager_port', '8042')
history_port = default('configurations/hue/history_port', '19888')

hdfs_port = namenode_rpc_port
webhdfs_port = namenode_http_port
yarn_rpc_port = jt_rpc_port
hive_port = hive_port
oozie_port = oozie_server_port
hcat_port = templeton_port

############## OTHERS ######################

import random, string
# new random key with each reconfigure ... I hope this is OK!
secret_key = ''.join(
    [random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(random.randint(40, 55))])

