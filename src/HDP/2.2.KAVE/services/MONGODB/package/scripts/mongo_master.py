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
import os

from resource_management import *
from mongo_base import MongoBase


class MongoMaster(MongoBase):
    mongo_packages = ['mongodb-org']

    def install(self, env):
        import params
        env.set_params(params)
        self.installMongo(env)
        self.configure(env)

    def configure(self, env):
        import params
        env.set_params(params)
        self.configureMongo(env)

    def start(self, env):
        print "start mongodb"
        self.configure(env)
        # TODO: Ambari 2.0 method should be replacing the below call
        # since Ambari 1.7.3 execute method never returns the control to script
        # So, we use nohup to detacht he start process, and we also need to redirect all the input and output
        Execute('nohup service mongod start  2> /dev/null > /dev/null < /dev/null &')

        # Start replication if it has a valid replicaset and at least 2 members (min 3 recommended)
        setname = default('configurations/mongodb/setname', 'None')
        if setname not in ["None", "False"]:
            mongo_hosts = default('/clusterHostInfo/mongodb_master_hosts', ['unknown'])
            print mongo_hosts
            if len(mongo_hosts) > 1:
                # write the configuration document to a file
                f = open('replicaset_conf.js', 'w')
                f.writelines([
                    'config =\n',
                    '{\n',
                    '"_id" : "', setname, '",\n',
                    '"members" : [\n'
                ])
                for i in range(len(mongo_hosts)):
                    f.writelines([
                        '{\n',
                        '"_id" :', str(i), ', "host" : "', mongo_hosts[i], '"\n'
                        '}'
                    ])
                    if i < len(mongo_hosts) - 1:
                        f.write(',\n')
                    else:
                        f.write('\n')
                    f.writelines([
                        ']\n',
                        '}\n',
                        'rs.initiate(config)'
                    ])
                # insert the document into the primary worker node to start replication
                Execute('mongo --host replica-001 < replicaset_conf.js')

    def stop(self, env):
        print "stop services.."
        Execute('service mongod stop')

    def restart(self, env):
        """MongoDB service is not very quick to shut down.
        Restarting without waiting for stop is causes quite a few problems along the lines of
           'cannot bind to port blah already in use.'
        A specific restart method is useful to ensure ambari waits between start and stop.
        """
        # Stop first
        print "restart mongodb"
        self.stop(env)
        # 3 seconds seems long enough in most cases to wait for the stop
        import time
        time.sleep(3)
        # now configure and start normally
        self.start(env)

    def status(self, env):
        print "checking status..."
        Execute('service mongod status')


if __name__ == "__main__":
    MongoMaster().execute()
