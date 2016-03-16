#!/usr/bin/env python
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
from resource_management import *
import kavecommon as kc
import os


class SonarQubeRunner(Script):
    installer_cache_path = '/tmp/'
    package = 'sonar-runner-dist-2.4.zip'

    def install(self, env):
        import params

        self.install_packages(env)

        # protect against client downloading behind firewall
        if not os.path.exists(params.sonarqube_runner_install_directory + '/current'):
            kc.copyCacheOrRepo(self.package, arch="noarch")
            Execute('mkdir -p %s ' % params.sonarqube_runner_install_directory)
            Execute('unzip -o -q %s -d %s' % (self.package, params.sonarqube_runner_install_directory))
            Execute('ln -sfn %s/sonar-runner-2.4 %s/current' % (
                params.sonarqube_runner_install_directory,
                params.sonarqube_runner_install_directory))

        self.configure(env)

    def configure(self, env):
        import params

        env.set_params(params)
        File(params.sonarqube_runner_install_directory + "/current/conf/sonar-runner.properties",
             content=Template("sonar-runner.properties.j2"),
             mode=0644
             )
        File('/etc/profile.d/sonar-runner.sh',
             content=Template("sonar-runner.sh.j2"),
             mode=0755
             )


if __name__ == "__main__":
    SonarQubeRunner().execute()
