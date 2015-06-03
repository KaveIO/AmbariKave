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

storm_zookeeper_servers = config['configurations']['stormsd']['storm.zookeeper.servers'].replace(", "," ").replace(","," ")
nimbus_host = config['configurations']['stormsd']['nimbus.host']
drpc_servers = config['configurations']['stormsd']['drpc.servers'].replace(", "," ").replace(","," ")

storm_zookeeper_port = default('configurations/stormsd/storm.zookeeper.port', "2181")
nimbus_childopts = default('configurations/stormsd/nimbus.childopts', '-Xmx1024m -Djava.net.preferIPv4Stack=true')
ui_port = default('configurations/stormsd/ui.port', "8744")
ui_childopts = default('configurations/stormsd/ui.childopts', '-Xmx768m -Djava.net.preferIPv4Stack=true')
supervisor_slots_ports = default('configurations/stormsd/supervisor.slots.ports', '6700, 6701').replace(", "," ").replace(","," ")
supervisor_childopts = default('configurations/stormsd/supervisor.childopts', '-Djava.net.preferIPv4Stack=true')
worker_childopts = default('configurations/stormsd/worker.childopts', '-Xmx768m -Djava.net.preferIPv4Stack=true')
drpc_childopts = default('configurations/stormsd/drpc.childopts', '-Xmx768m -Djava.net.preferIPv4Stack=true')
log_level = default('configurations/stormsd/log_level', 'WARN')
