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
from resource_management.core.exceptions import ComponentIsNotRunning


class LcmServer(Script):
    sttmpdir = '/tmp/lcm_install_dump' 

    def install(self, env):
        import params
        import os
        print "Installing LCM Server:"
        super(LcmServer, self).install(env)
        packagefileonly = 'lcm-complete-' + params.lcm_releaseversion
        package = packagefileonly + '-bin.tar'
        if len(self.sttmpdir) < 4:
            raise IOError("where are you using for temp??")
        Execute("mkdir -p " + self.sttmpdir)
        Execute("rm -rf " + self.sttmpdir + "/*")

        # Create service user, config/home dir and set permissions
        Execute('id -u ' + params.lcm_service_user +
                ' &>/dev/null || useradd -r -s /sbin/nologin ' + params.lcm_service_user)
        Execute('mkdir -p ' + params.lcm_install_dir )
#        Execute('chown -R ' + params.lcm_service_user +
#                ':root ' + params.lcm_install_dir )

        os.chdir(self.sttmpdir)
#        copy_cache_or_repo shall be used when we have an official release of LCM
#        kc.copy_cache_or_repo(package, arch='noarch', ver=params.releaseversion, dir="Eskapade")
        Execute('wget ' +
                'http://repos:kaverepos@repos.dna.kpmglab.com/noarch/LocalCatalogManager/nightly/' + package)
        Execute('tar -xf ' + package + ' -C ' + params.lcm_install_dir )
        kc.chown_r(params.lcm_install_dir, params.lcm_service_user)
        
        
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
        File(lcm_config_dir + 'log4j-server.properties',
             content=InlineTemplate(params.log4j_server_properties),
             mode=0600
             )
        File(lcm_config_dir + 'log4j-ui.properties',
             content=InlineTemplate(params.log4j_ui_properties),
             mode=0600
             )
        File(lcm_config_dir + 'log4j-ui.properties',
             content=InlineTemplate(params.log4j_ui_properties),
             mode=0600
             )
        File(params.systemd_lcmserver_unitfile_path,
             content=Template("lcm-server.service"),
             mode=0600
             )
        File(params.systemd_lcmserver_unitfile_path,
             content=Template("lcm-server.service"),
             mode=0600
             )
           
      
    def start(self, env):
        import params
        import os

        self.configure(env)
        Execute('systemctl start lcm-server')

    def stop(self, env):
        import os

        Execute('systemctl stop lcm-server')


    def restart(self, env):
        import os
        self.configure(env)
        Execute('systemctl restart lcm-server')


    def status(self, env):
        import params
        import subprocess

        check = subprocess.Popen('systemctl is-active --quiet lcm-server', shell=True)
        check.wait()
        if int(check.returncode) != 0:
           raise ComponentIsNotRunning()
        return True
        
if __name__ == "__main__":
    LcmServer().execute()
