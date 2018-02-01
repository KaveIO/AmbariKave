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

    def install(self, env):
        import params
        import os
        
        print "Installing LCM Server:"
        super(LcmServer, self).install(env)
        package = 'lcm-complete-' + params.lcm_releaseversion + '-bin.tar'
        self.configure(env)
        if len(self.sttmpdir) < 4:
            raise IOError("where are you using for temp??")
        Execute("mkdir -p " + self.sttmpdir)
        Execute("rm -rf " + self.sttmpdir + "/*")
        installdir = params.lcm_destination_dir + '/' + params.lcm_releaseversion 

        # Create service user, config/home dir and set permissions
        Execute('id -u ' + params.lcm_service_user +
                'airflow &>/dev/null || useradd -r -s /sbin/nologin ' + params.lcm_service_user)
        Execute('mkdir -p ' + params.lcm_destination_dir)
        Execute('chown -R ' + params.lcm_service_user +
                ':root' + params.lcm_destination_dir)

        os.chdir(self.sttmpdir)
#        copy_cache_or_repo shall be used when we have an official release of LCM
#        kc.copy_cache_or_repo(package, arch='noarch', ver=params.releaseversion, dir="Eskapade")
        Execute('wget ' +
                'http://repos:kaverepos@repos.dna.kpmglab.com/noarch/LocalCatalogManager/nightly/' + package)
        Execute('tar -xzf ' + package + ' -C ' + installdir)
        kc.chown_r(installdir, params.lcm_service_user)
        
        
    def configure(self, env):
        import params
        import os
        env.set_params(params)
        File(self.airflow_config_path,
             content=InlineTemplate(params.airflow_conf),
             mode=0755
             )
        File(self.systemd_env_init_path,
             content=Template("airflow"),
             mode=0755
             )
        File(self.systemd_schd_unitfile_path,
             content=Template("airflow-scheduler.service"),
             mode=0755
             )
        File(self.systemd_ws_unitfile_path,
             content=Template("airflow-webserver.service"),
             mode=0755
             )

        super(Airflow, self).configure(env)
        
    def start(self, env):
        import params
        import os

        self.configure(env)
        Execute('systemctl start airflow-webserver')
        Execute('systemctl start airflow-scheduler')

    def stop(self, env):
        import params
        import os

        Execute('systemctl stop airflow-webserver')
        Execute('systemctl stop airflow-scheduler')

    def restart(self, env):

        self.configure(env)
        Execute('systemctl restart airflow-webserver')
        Execute('systemctl restart airflow-scheduler')

    def status(self, env):
        import params
        import os

        Execute('systemctl status airflow-webserver')


if __name__ == "__main__":
    Airflow().execute()
