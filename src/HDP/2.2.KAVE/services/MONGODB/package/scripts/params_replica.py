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

db_path = default('configurations/mongodb/db_path', '/var/lib/mongo')
logpath = default('configurations/mongodb/logpath', '/var/log/mongodb/mongod.log')
bind_ip = default('configurations/mongodb/bind_ip', '0.0.0.0')
tcp_port = default('configurations/mongodb/tcp_port', '27017')
setname = default('configurations/mongodb/setname', 'rs0')
# The web status page is always accessible at a port number that is 1000 greater than the port determined by tcp_port.
mongo_host = default('/clusterHostInfo/mongodb_master_hosts', ['unknown'])[0]
if mongo_host=="unknown":
    if bind_ip not in ['0.0.0.0','127.0.0.1']:
        mongo_host=bind_ip
if mongo_host==hostname:
    mongo_host='localhost'
