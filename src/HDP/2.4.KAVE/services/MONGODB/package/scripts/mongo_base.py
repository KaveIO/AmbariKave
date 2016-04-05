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


class MongoBase(Script):
    repos_file_path = '/etc/yum.repos.d/mongodb.repo'
    config_file_path = '/etc/mongod.conf'
    mongo_packages = None

    def installMongo(self, env):
        import params

        env.set_params(params)

        self.install_packages(env)

        if os.path.exists(self.repos_file_path):
            print "File exists"
        else:
            print "file not exists"
            File(self.repos_file_path,
                 content=Template("mongodb.repo"),
                 mode=0644
                 )
#          File(self.repos_file_path,
#               content=InlineTemplate(params.mongo_db_repo),
#               mode=0644
#               )
        print "installing mongodb..."
        if self.mongo_packages is not None and len(self.mongo_packages):
            for pack in self.mongo_packages:
                Package(pack)

    def configureMongo(self, env):
        import params

        env.set_params(params)
#        File(self.config_file_path,
#             content=Template("mongod.conf.j2"),
#             mode=0644
#             )
        File(self.config_file_path,
             content=InlineTemplate(params.mongodb_conf),
             mode=0644
             )
