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
import kavecommon as kc


class KaveGanglia(Script):

    def install(self, env):
        import params

        env.set_params(params)
        self.install_packages(env)
        Package('ganglia-gmetad')
        self.configure(env)

    def configure(self, env):
        import params
        import kavecommon as kc

        env.set_params(params)
        Execute('chkconfig gmetad on')

    def start(self, env):
        self.configure(env)
        Execute("service gmetad start")

    def stop(self, env):
        Execute("service gmetad stop")

    def status(self, env):
        print Execute("service gmetad status")


if __name__ == "__main__":
    KaveGanglia().execute()
