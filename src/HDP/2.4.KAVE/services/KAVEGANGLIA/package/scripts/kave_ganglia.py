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


class KaveGanglia(kc.ApacheScript):
    gmetad_config_path = "/etc/ganglia/gmetad.conf"
    gmetad_init_path = "/etc/init.d/gmetad"
    ganglia_config_path = "/etc/httpd/conf.d/ganglia.conf"

    def install(self, env):
        import params
        Package('httpd')

        super(KaveGanglia, self).install(env)
        env.set_params(params)
        self.install_packages(env)
        Package('ganglia-gmetad')
        Package('rrdtool')
        self.configure(env)

    def configure(self, env):
        import params
        import kavecommon as kc

        env.set_params(params)
        File(self.ganglia_config_path,
             content=InlineTemplate(params.kaveganglia_conf),
             mode=0755
             )
        File(self.gmetad_config_path,
             content=Template("gmetad.conf.j2"),
             mode=0755
             )
        File(self.gmetad_init_path,
             content=InlineTemplate(params.kaveganglia_gmetad_conf),
             mode=0755
             )
        Execute('chkconfig gmetad on')
        if os.path.exists("/var/lib/ganglia/rrds"):
            Execute('chown -R nobody:nobody /var/lib/ganglia/rrds')

        super(KaveGanglia, self).configure(env)

    def start(self, env):
        self.configure(env)
        Execute("service gmetad start")
        super(KaveGanglia, self).start(env)

    def stop(self, env):
        Execute("service gmetad stop")
        super(KaveGanglia, self).stop(env)

    def status(self, env):
        super(KaveGanglia, self).status(env)
        Execute("service gmetad status")


if __name__ == "__main__":
    KaveGanglia().execute()
