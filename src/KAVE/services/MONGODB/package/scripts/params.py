##############################################################################
#
# Copyright 2016 KPMG Advisory N.V. (unless otherwise stated)
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
import kavecommon as kc

config = Script.get_config()
hostname = config["hostname"]

db_path = kc.default('configurations/mongodb/db_path', '/var/lib/mongo', kc.is_valid_directory)
logpath = kc.default('configurations/mongodb/logpath', '/var/log/mongodb/mongod.log', kc.is_valid_directory)
bind_ip = kc.default('configurations/mongodb/bind_ip', '0.0.0.0', kc.is_valid_ipv4_address)
tcp_port = kc.default('configurations/mongodb/tcp_port', '27017', kc.is_valid_port)
setname = default('configurations/mongodb/setname', 'None')

mongodb_baseurl = default('configurations/mongodb/mongodb_baseurl',
                          'https://repo.mongodb.org/yum/redhat/$releasever/mongodb-org/3.6/x86_64/')


# The web status page is always accessible at a port number that is 1000 greater than the port determined by tcp_port.

mongo_hosts = default('/clusterHostInfo/mongodb_master_hosts', ['unknown'])
mongo_host = mongo_hosts[0]

mongo_arbiter_hosts = default('/clusterHostInfo/mongodb_arbiter_hosts', [])
is_arbiter = (mongo_arbiter_hosts is not None) and (hostname in mongo_arbiter_hosts)

# This is carried over from previous single mongod config, probably needs reworking
if mongo_host == "unknown":
    if bind_ip not in ['0.0.0.0', '127.0.0.1']:
        mongo_host = bind_ip
if mongo_host == hostname:
    mongo_host = 'localhost'

if setname in ["None", "False"]:
    if len(mongo_hosts) < 2:
        setname = ""

set_with_arbiters = (len(mongo_arbiter_hosts) > 0 and setname not in [None, False, "None", "False", ""])

mongodb_conf = default('configurations/mongodb/mongodb_conf', """
# mongod.conf

# for documentation of all options, see:
#   http://docs.mongodb.org/manual/reference/configuration-options/

# where to write logging data.
systemLog:
  destination: file
  logAppend: true
  path: {{logpath}}

# Where and how to store data.
storage:
  dbPath: {{db_path}}
  journal:
    enabled: true
#  engine:
#  mmapv1:
#  wiredTiger:

# how the process runs
processManagement:
  fork: true  # fork and run in background
  pidFilePath: /var/run/mongodb/mongod.pid  # location of pidfile
  timeZoneInfo: /usr/share/zoneinfo

# network interfaces
net:
  port: {{tcp_port}}
  bindIp: {{bind_ip}}  # Listen to local interface only, comment to listen on all interfaces.


#security:

#operationProfiling:

#replication:

#sharding:

## Enterprise-Only Options

#auditLog:

#snmp:
""")

replica_config_params = {"_id": setname, "members": []}
init_id = 0
for _host in mongo_hosts:
    replica_config_params["members"].append({"_id": init_id,
                                             "host": _host + ":" + str(tcp_port)})
    init_id = init_id + 1

if set_with_arbiters:
    for _host in mongo_arbiter_hosts:
        replica_config_params["members"].append({"_id": init_id,
                                                 "host": _host + ":" + str(tcp_port),
                                                 "arbiterOnly": True})
        init_id = init_id + 1

import json
replica_config_params = json.dumps(replica_config_params)
replica_config_params.replace("True", 'true')
