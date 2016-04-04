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
import sys
import os
import shutil

from resource_management import *


class KaveToolbox(Script):
    sttmpdir = "/tmp/kavetoolbox_install/dump"
    kind = "node"

    def install(self, env):
        import params
        import kavecommon as kc

        self.install_packages(env)
        env.set_params(params)
        # no need to install if already installed ... does not work behind firewall after restart
        if self.kind == "node" and (os.path.exists('/etc/kave/toolbox_ok')
                                    and os.path.exists(params.top_dir + '/KaveToolbox')):
            return True
        # configure first before installing, create custom install file and mirror file if necessary
        self.configure(env)
        if len(self.sttmpdir) < 4:
            raise IOError("where are you using for temp??")
        # Set up temporary directory for download/install
        Execute("mkdir -p " + self.sttmpdir)
        Execute("rm -rf " + self.sttmpdir + "/*")
        topdir = os.path.realpath(os.path.curdir)
        extraopts = ""
        if params.ignore_missing_groups:
            extraopts = " --ignore-missing-groups"
        kavetoolbox_path = '/KaveToolbox/' + params.releaseversion + 'scripts/KaveInstall'
        instscript = params.top_dir + kavetoolbox_path
        # no need to download if install script already exists
        if not os.path.exists(instscript):
            os.chdir(self.sttmpdir)
            kc.copyCacheOrRepo('kavetoolbox-' + params.releaseversion + '.tar.gz', arch="noarch",
                               ver=params.releaseversion,
                               dir="KaveToolbox")
            Execute('tar -xzf kavetoolbox-' + params.releaseversion + '.tar.gz')
            # try to cope with the annoying way the tarball contains something with .git at the end!
            import glob

            for gits in glob.glob(self.sttmpdir + "/*.git"):
                if os.path.isdir(gits) and not gits.endswith("/.git"):
                    Execute('mv ' + gits + ' ' + gits[:-len(".git")])
#            instscript = './KaveToolbox/scripts/KaveInstall'
            instscript = '.' + kavetoolbox_path

        commandlineargs = " " + params.command_line_args
        Execute(instscript + ' --' + self.kind + extraopts + commandlineargs)
        os.chdir(topdir)
        Execute("rm -rf " + self.sttmpdir + "/*")
        Execute("mkdir -p /etc/kave")
        Execute('touch /etc/kave/toolbox_ok')
        Execute('chmod -R a+r /etc/kave')

    def configure(self, env):
        import params

        env.set_params(params)
        Execute("mkdir -p /etc/kave")
        Execute("chmod -R a+r /etc/kave")
        Execute("chmod a+x /etc/kave")
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
        File("/etc/kave/CustomInstall.py",
             content=InlineTemplate(params.custom_install_template),
             mode=0644
             )
        Execute("chmod -R a+r /etc/kave")


if __name__ == "__main__":
    KaveToolbox().execute()
