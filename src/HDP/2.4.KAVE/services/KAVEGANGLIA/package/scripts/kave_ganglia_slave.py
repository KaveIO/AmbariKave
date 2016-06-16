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


class KaveGangliaSlave(Script):
    gmond_config_path = "/etc/ganglia/gmond.conf"
    gmond_init_path = "/etc/init.d/gmond"
    ganglia_config_path = "/etc/httpd/conf.d/ganglia.conf"

    def install(self, env):
        import params

        env.set_params(params)
        self.install_packages(env)
        self.configure(env)

    def configure(self, env):
        import params
        import kavecommon as kc

        env.set_params(params)
        File(self.ganglia_config_path,
             content=InlineTemplate(params.kaveganglia_conf),
             mode=0755
             )
        File(self.gmond_config_path,
             content=InlineTemplate(params.kaveganglia_gmond_conf),
             mode=0755
             )
        File(self.gmond_init_path,
             content=Template("gmond.j2"),
             mode=0755
             )
        Execute('chkconfig gmond on')
        if os.path.exists("/var/lib/ganglia/rrds"):
            Execute('chown -R nobody:nobody /var/lib/ganglia/rrds')

    def start(self, env):
        self.configure(env)
        Execute("service gmond start")

    def stop(self, env):
        Execute("service gmond stop")

    def status(self, env):
        print Execute("service gmond status")


if __name__ == "__main__":
    KaveGangliaSlave().execute()
