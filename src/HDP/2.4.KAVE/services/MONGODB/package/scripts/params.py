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
setname = default('configurations/mongodb/setname', 'None')

mongodb_baseurl = default('configurations/mongodb/mongodb_baseurl',
                          'https://repo.mongodb.org/yum/redhat/6/mongodb-org/stable/x86_64/')


# The web status page is always accessible at a port number that is 1000 greater than the port determined by tcp_port.

mongo_hosts = default('/clusterHostInfo/mongodb_master_hosts', ['unknown'])
mongo_host = mongo_hosts[0]

# This is carried over from previous single mongod config, probably needs reworking
if mongo_host == "unknown":
    if bind_ip not in ['0.0.0.0', '127.0.0.1']:
        mongo_host = bind_ip
if mongo_host == hostname:
    mongo_host = 'localhost'

if setname in ["None", "False"]:
    if len(mongo_hosts) < 2:
        setname = ""

mongodb_conf = default('configurations/mongodb/mongodb_conf', """
# mongod.conf

#where to log
logpath={{logpath}}

logappend=true

# fork and run in background
fork=true

#which port to listen for client connections?
port={{tcp_port}}
#
# The web status page is always accessible at a port number that is 1000 greater than the port determined by port.
#

#where to store the database?
dbpath={{db_path}}

# location of pidfile
pidfilepath=/var/run/mongodb/mongod.pid

# Listen to local interface only. Comment out to listen on all interfaces.
# bind_ip=127.0.0.1
bind_ip={{bind_ip}}

# Disables write-ahead journaling
# nojournal=true

# Enables periodic logging of CPU utilization and I/O wait
#cpu=true

# Turn on/off security.  Off is currently the default
#noauth=true
#auth=true

# Verbose logging output.
#verbose=true

# Inspect all client data for validity on receipt (useful for
# developing drivers)
#objcheck=true

# Enable db quota management
#quota=true

# Set oplogging level where n is
#   0=off (default)
#   1=W
#   2=R
#   3=both
#   7=W+some reads
#diaglog=0

# Ignore query hints
#nohints=true

# Enable the HTTP interface (Defaults to port 28017).
httpinterface=true

# Turns off server-side scripting.  This will result in greatly limited
# functionality
#noscripting=true

# Turns off table scans.  Any query that would do a table scan fails.
#notablescan=true

# Disable data file preallocation.
#noprealloc=true

# Specify .ns file size for new databases.
# nssize={{size}}

# Replication Options

# in replicated mongo databases, specify the replica set name here
replSet={{setname}}
# maximum size in megabytes for replication operation log
#oplogSize=1024
# path to a key file storing authentication info for connections
# between replica set members
#keyFile=/path/to/keyfile """)
