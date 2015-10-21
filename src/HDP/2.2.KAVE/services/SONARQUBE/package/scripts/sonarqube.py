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
import os
import subprocess
import kavecommon as kc
from resource_management import *


class SonarQube(Script):
    installer_cache_path = '/tmp/'
    package = 'sonarqube-5.0.1.zip'
    # sonar_mirror='http://dist.sonar.codehaus.org/sonarqube-5.0.1.zip'

    def install(self, env):
        import params

        env.set_params(params)
        self.install_packages(env)
        # protect against client downloading behind firewall
        if not os.path.exists(params.sonarqube_install_directory + '/current'):
            kc.copyCacheOrRepo(self.package, arch="noarch")  # http://dist.sonar.codehaus.org/sonarqube-5.0.1.zip
            Execute('mkdir -p %s ' % params.sonarqube_install_directory)
            Execute('unzip -o -q %s -d %s' % (self.package, params.sonarqube_install_directory))
            Execute('ln -sfn %s/sonarqube-5.0.1 %s/current' % (
                params.sonarqube_install_directory,
                params.sonarqube_install_directory))

        if not os.path.exists(params.sonarqube_install_directory+'/current/extensions/plugins/sonar-pam-plugin-0.2.jar'):
            import tempfile
            tdir=tempfile.mkdtemp()
            topd=os.path.realpath('.')
            os.chdir(tdir)
            Execute('wget http://downloads.sourceforge.net/project/jpam/jpam/jpam-1.1/JPam-Linux_amd64-1.1.tgz -O JPam-Linux_amd64-1.1.tgz')
            Execute('tar -xvzf JPam-Linux_amd64-1.1.tgz')
            Execute('cp JPam-1.1/JPam-1.1.jar '+params.sonarqube_install_directory+'/current/lib/common/')
            Execute('cp JPam-1.1/libjpam.so /usr/lib/jvm/jre-1.7.0-openjdk.x86_64/lib/amd64/')
            Execute('chmod a+x /usr/lib/jvm/jre-1.7.0-openjdk.x86_64/lib/amd64/libjpam.so')
            Execute('cp JPam-1.1/net-sf-jpam /etc/pam.d/')
            Execute('wget http://downloads.sonarsource.com/plugins/org/codehaus/sonar-plugins/sonar-pam-plugin/0.2/sonar-pam-plugin-0.2.jar -O '
                    +params.sonarqube_install_directory+'/current/extensions/plugins/sonar-pam-plugin-0.2.jar')
            os.chdir(topd)
            Execute('rm -rf '+tdir)

        # Getting the processor architecture type(64 bit or 32 bit)
        p = subprocess.Popen(["uname", "-p"], stdout=subprocess.PIPE)
        arch_type = p.communicate()[0]
        if os.path.exists('/etc/init.d/sonar'):
            Execute('rm -rf /etc/init.d/sonar')
        if 'x86_64' in arch_type:
            print("64 bit processor")
            Execute('ln -s %s/current/bin/linux-x86-64/sonar.sh /etc/init.d/sonar' % params.sonarqube_install_directory)
        else:
            print("32 bit processor")
            Execute('ln -s %s/current/bin/linux-x86-32/sonar.sh /etc/init.d/sonar' % params.sonarqube_install_directory)

        for plugin in params.sonarqube_plugins:
            kc.copyCacheOrRepo(plugin, arch="noarch")
            Execute('mv %s %s/current/extensions/plugins/' % (plugin, params.sonarqube_install_directory))

        self.configure(env)

    def start(self, env):
        self.configure(env)
        Execute('service sonar start > /dev/null')

    def stop(self, env):
        Execute('service sonar stop')

    def restart(self, env):
        self.configure(env)
        Execute('service sonar restart > /dev/null')

    def status(self, env):
        Execute('service sonar status')

    def configure(self, env):
        import params

        env.set_params(params)
        Execute('mkdir -p %s ' % (params.sonarqube_install_directory + "/current/conf"))
        File(params.sonarqube_install_directory + "/current/conf/sonar.properties",
             content=Template("sonar.properties.j2"),
             mode=0644
             )


if __name__ == "__main__":
    SonarQube().execute()
