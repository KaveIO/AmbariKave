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
import os
import sys

from resource_management import *
from mongo_base import MongoBase
import kavecommon as kc


class MongoMaster(MongoBase):
    mongo_packages = ['mongodb-org']

    def install(self, env):
        import params
        env.set_params(params)
        self.install_mongo(env)
        Execute("mkdir -p " + params.db_path)
        kc.chown_r(params.db_path, 'mongod')
    def configure(self, env):
        import params
        env.set_params(params)
        self.configure_mongo(env)

    def start(self, env):
        print "start mongodb"
        self.configure(env)
        Execute('service mongod start', wait_for_finish=False)

        # Start replication if it has a valid replicaset and at least 2 members (min 3 recommended)
        import params
        if params.setname and params.setname not in ["None", "False"]:
            if len(params.mongo_hosts) > 1 and not params.is_arbiter:
                # write the configuration document to a file,
                # never run this from the arbiter! That will never work!
                File('/tmp/replicaset_conf.js',
                     content=Template("mongo_replication.conf.j2"),
                     mode=0644
                     )
                # insert the document into the primary worker node to start replication
                print 'wait for service start before adding replica config (300s)'
                sys.stdout.flush()
                import time
                time.sleep(300)
                Execute('mongo < /tmp/replicaset_conf.js > /tmp/replicaset_debug.txt 2>&1&')

    def stop(self, env):
        print "stopping mongodb.."
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
        import subprocess

        check = subprocess.Popen('systemctl is-active --quiet mongod', shell=True)
        check.wait()
        if int(check.returncode) != 0:
            raise ComponentIsNotRunning()
        return True
if __name__ == "__main__":
    MongoMaster().execute()
