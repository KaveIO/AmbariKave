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
    gmetad_config_path = "/etc/ganglia/getmad.conf"
    gmetad_init_path = "/etc/init.d/gmetad"
    ganglia_conf_path = "/etc/httpd/conf.d/ganglia.conf"

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
        File(self.ganglia_config_path,
             content=Template("ganglia.conf.j2"),
             mode=0644
             )
        File(self.gmetad_config_path,
             content=Template("gmetad.conf.j2"),
             mode=0644
             )
        File(self.gmetad_init_path,
             content=Template("gmetad.j2"),
             mode=0644
             )
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
