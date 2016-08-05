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

from resource_management import *
from mongo_master import MongoMaster


class MongoArbiter(MongoMaster):

    def start(self, env):
        import params
        if not params.setname or params.setname in ["None", "False"]:
            raise ValueError("An arbiter needs to be told what setname to attach to")
        super(MongoArbiter, self).start(env)


if __name__ == "__main__":
    MongoArbiter().execute()
