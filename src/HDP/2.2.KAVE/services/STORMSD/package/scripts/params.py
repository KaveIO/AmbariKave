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

config = Script.get_config()
storm_conf_file = "/usr/local/storm/conf/storm.yaml"
hostname = config["hostname"]

# config['configurations']['stormsd']['stormsd.zookeeper.servers'].replace(", "," ").replace(","," ").split()
storm_zookeeper_servers = default("/clusterHostInfo/zookeeper_hosts", None)
nimbus_host = default("/clusterHostInfo/nimbus_sd_master_hosts", [None])[0]
# config['configurations']['stormsd']['stormsd.drpc.servers'].replace(", "," ").replace(","," ").split()
drpc_servers = default("/clusterHostInfo/stormsd_drpc_server_hosts", False)
use_drpc = (drpc_servers is not False)
if None in [storm_zookeeper_servers, nimbus_host]:
    raise NameError("Could not find required services from clusterHostInfo : " + str(config['clusterHostInfo']))

# find/replace localhost
if nimbus_host == hostname:
    nimbus_host = "localhost"
storm_zookeeper_servers = [s if s != hostname else 'localhost' for s in storm_zookeeper_servers]

if use_drpc:
    drpc_servers = [s if s != hostname else 'localhost' for s in drpc_servers]

storm_zookeeper_port = default('configurations/stormsd/stormsd.zookeeper.port', "2181")
nimbus_childopts = default('configurations/stormsd/stormsd.nimbus.childopts',
                           '-Xmx1024m -Djava.net.preferIPv4Stack=true')
ui_port = default('configurations/stormsd/stormsd.ui.port', "8744")
ui_childopts = default('configurations/stormsd/stormsd.ui.childopts', '-Xmx768m -Djava.net.preferIPv4Stack=true')
supervisor_slots_ports = default('configurations/stormsd/stormsd.supervisor.slots.ports',
                                 '6700, 6701').replace(", ", " ").replace(",", " ").split()
supervisor_childopts = default('configurations/stormsd/stormsd.supervisor.childopts', '-Djava.net.preferIPv4Stack=true')
worker_childopts = default('configurations/stormsd/stormsd.worker.childopts',
                           '-Xmx768m -Djava.net.preferIPv4Stack=true')
drpc_childopts = default('configurations/stormsd/stormsd.drpc.childopts', '-Xmx768m -Djava.net.preferIPv4Stack=true')
log_level = default('configurations/stormsd/stormsd.loglevel', 'WARN')
stormpackage=default('http://ftp.yz.yamagata-u.ac.jp/pub/network/apache/storm/apache-storm-0.10.0/apache-storm-0.10.0.zip',None)
