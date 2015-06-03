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
    mongo_packages=['mongodb-org']

    def install(self, env):
        import params
        env.set_params(params)
        self.installMongo(env)
        self.configure(env)

    def configure(self,env):
        import params
        env.set_params(params)
        self.configureMongo(env)

    def start(self, env):
        print "start mongodb"
        Execute('service mongod start > /dev/null ')

    def stop(self, env):
        print "stop services.."
        Execute('service mongod stop')

    def restart(self, env):
        print "restart mongodb"
        Execute('service mongod restart > /dev/null ')

    def status(self, env):
        print "checking status..."
        Execute('service mongod status')


if __name__ == "__main__":
    MongoMaster().execute()
