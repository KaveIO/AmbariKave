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

class MongoClient(MongoBase):
    client_config_path="/etc/mongoclient.conf"
    mongo_packages=['mongodb-org-shell', 'mongodb-org-tools']

    def install(self, env):
        import params
        env.set_params(params)
        self.installMongo(env)
        self.configure(env)

    def configure(self,env):
        import params
        env.set_params(params)
        self.configureMongo(env)
        File(self.client_config_path,
             content=Template("mongoclient.conf.j2"),
             mode=0644
             )


if __name__ == "__main__":
    MongoClient().execute()
