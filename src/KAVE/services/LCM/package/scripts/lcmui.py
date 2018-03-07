##############################################################################
#
# Copyright 2018 KPMG Advisory N.V. (unless otherwise stated)
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
from resource_management.core.exceptions import ComponentIsNotRunning


class LcmWebUI(Script):
    sttmpdir = '/tmp/lcm_install_dump'

    def install(self, env):
        import params
        import os
        print "Installing LCM Web User Interface:"
        super(LcmWebUI, self).install(env)
        packagefileonly = 'lcm-complete-' + params.lcm_releaseversion
        package = packagefileonly + '-bin.tar'
        if len(self.sttmpdir) < 4:
            raise IOError("where are you using for temp??")

        if not os.path.isfile(params.lcm_home_dir + 'bin/start-ui.sh'):
            raise EnvironmentError('LCM UI startup script not found at ' +
                                   params.lcm_home_dir + '/bin' +
                                   ' Is LCM server installed on this system?')

    def configure(self, env):
        import params
        import os
        env.set_params(params)
        lcm_config_dir = params.lcm_home_dir + 'config/'
        File(lcm_config_dir + 'application.properties',
             content=InlineTemplate(params.application_properties),
             mode=0600
             )
        File(lcm_config_dir + 'security.properties',
             content=InlineTemplate(params.security_properties),
             mode=0600
             )
        File(lcm_config_dir + 'log4j-ui.properties',
             content=InlineTemplate(params.log4j_ui_properties),
             mode=0600
             )
        File(params.systemd_lcmui_unitfile_path,
             content=Template("lcm-ui.service"),
             mode=0600
             )

    def start(self, env):
        import params
        import os

        self.configure(env)
        Execute('systemctl start lcm-ui')

    def stop(self, env):
        import os
        Execute('systemctl stop lcm-ui')

    def restart(self, env):
        import os
        self.configure(env)
        Execute('systemctl restart lcm-ui')

    def status(self, env):
        import subprocess
        check = subprocess.Popen('systemctl is-active --quiet lcm-ui', shell=True)
        check.wait()
        if int(check.returncode) != 0:
            raise ComponentIsNotRunning()
        return True


if __name__ == "__main__":
    LcmWebUI().execute()
