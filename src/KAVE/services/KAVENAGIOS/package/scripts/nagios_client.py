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
import subprocess
from resource_management import *
import kavecommon as kc


class NagiosClient(Script):
    nagios_client_nrpe_file = "/etc/nagios/nrpe.cfg"

    def install(self, env):
        import params
        env.set_params(params)
        self.install_packages(env)
        kc.install_epel()
        Execute('yum -y install nrpe')
        Execute('yum -y install nagios-plugins-all')
        Execute('yum -y install openssl')
        self.configure(env)

    def configure(self, env):
        import params
        env.set_params(params)
        File(self.nagios_client_nrpe_file,
             content=InlineTemplate(params.nagios_client_nrpe_file),
             mode=0755
             )

    def start(self, env):
        import params
        env.set_params(params)
        Execute('systemctl start nrpe')
        Execute('chkconfig nrpe on')

    def stop(self, env):
        Execute("systemctl stop nrpe")

    def restart(self, env):
        Execute("systemctl restart nrpe")

    def status(self, env):
        check = subprocess.Popen('systemctl status nrpe', shell=True)
        check.wait()
        if int(check.returncode) != 0:
            raise ComponentIsNotRunning()
        return True

if __name__ == "__main__":
    NagiosClient().execute()
