#############################################################################
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
#############################################################################
import sys
import os
import shutil

from resource_management import *


class Eskapade(Script):
    sttmpdir = "/tmp/eskapade_install/dump"
    kind = "node"

    def status(self, env):
        raise ClientComponentHasNoStatus()

    def install(self, env):
        import params
        import kavecommon as kc
        Execute('yum clean all')
        self.install_packages(env)
        env.set_params(params)
        # no need to install if already installed ... does not work behind firewall after restart
        if self.kind == "node" and (os.path.exists('/etc/eskapade/eskapade_ok')
                                    and os.path.exists(params.top_dir + '/Eskapade')):
            return True
        # configure first before installing, create custom install file and mirror file if necessary
        self.configure(env)
        if len(self.sttmpdir) < 4:
            raise IOError("where are you using for temp??")
        # Set up temporary directory for download/install
        Execute("mkdir -p " + self.sttmpdir)
        Execute("rm -rf " + self.sttmpdir + "/*")
        topdir = os.path.realpath(os.path.curdir)
        eskapade_path = 'Eskapade/' + params.releaseversion + ''
        install_dir = params.top_dir + eskapade_path
        os.chdir(self.sttmpdir)
        kc.copy_cache_or_repo('Eskapade-' + params.releaseversion + '.tar.gz', arch='noarch',
                              ver=params.releaseversion,
                              dir="Eskapade")
        Execute('tar -xzf Eskapade-' + params.releaseversion + '.tar.gz')
        Execute('mkdir -p ' + install_dir)
        Execute('cp -R Eskapade-' + params.releaseversion + '/* ' + install_dir)
        os.chdir(install_dir)
        Execute("bash -c 'source /opt/KaveToolbox/pro/scripts/KaveEnv.sh &>/dev/null; pip install -r requirements.txt'")

        File("/etc/profile.d/eskapade.sh",
                 content=Template("eskapade.sh.j2", setup_script=install_dir + '/setup.sh'),
                 mode=0644
                 )
        os.chdir(topdir)
        Execute("rm -rf " + self.sttmpdir + "/*")
        Execute("mkdir -p /etc/eskapade")
        Execute('touch /etc/eskapade/eskapade_ok')
        Execute('chmod -R a+r /etc/eskapade')

    def configure(self, env):
        import params

        env.set_params(params)
        Execute("mkdir -p /etc/eskapade")
        Execute("chmod -R a+r /etc/eskapade")
        Execute("chmod a+x /etc/eskapade")
        alternatives = []
        if ',' in params.alternative_download:
            alternatives = [a.strip() for a in params.alternative_download.strip().split(',')]
        elif len(params.alternative_download.strip()):
            alternatives = [params.alternative_download.strip()]
        if len(alternatives):
            fexisting = open('/etc/kave/mirror')
            existing = fexisting.read()
            fexisting.close()
            f = open('/etc/kave/mirror', 'w')
            f.write((existing + '\n').replace('\n\n', '\n'))
            f.write('\n'.join(alternatives))
            f.write('\n')
            f.close()
        Execute("chmod -R a+r /etc/eskapade")

    def start(self, env):
        return True

    def stop(self, env):
        return True

    def restart(self, env):
        return True

if __name__ == "__main__":
    Eskapade().execute()
