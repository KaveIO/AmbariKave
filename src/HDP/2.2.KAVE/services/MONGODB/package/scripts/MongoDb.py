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


class MongoDb(Script):
    repos_file_path = '/etc/yum.repos.d/mongodb.repo'
    config_file_path = '/etc/mongod.conf'

    def install(self, env):

        self.install_packages(env)

        if os.path.exists(self.repos_file_path):
            print "File exists"
        else:
            print "file not exists"
            File(self.repos_file_path,
                 content=Template("mongodb.repo"),
                 mode=0644
                 )
        print "installing mongodb..."
        Package('mongodb-org')
        #Execute('yum install -y mongodb-org')
        self.configure(env)

    def start(self, env):
        print "start mongodb"
        Execute('service mongod start')

    def stop(self, env):
        print "stop services.."
        Execute('service mongod stop')

    def restart(self, env):
        print "restart mongodb"
        Execute('service mongod restart')

    def status(self, env):
        print "checking status..."
        Execute('service mongod status')

    def configure(self, env):
        File(self.config_file_path,
             content=Template("mongod.conf.j2"),
             mode=0644
             )


if __name__ == "__main__":
    MongoDb().execute()
