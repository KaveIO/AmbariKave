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
import sys
import os
import shutil
import subprocess

from resource_management import *


class KaveToolbox(Script):
    sttmpdir = "/opt/kavetoolbox_install/dump"
    kind = "node"
    status_file = "/etc/kave/status"

    def status(self, env):
        raise ClientComponentHasNoStatus()

    def install(self, env):
        import params
        import kavecommon as kc

        package = 'kavetoolbox-' + params.releaseversion + '.tar.gz'
        Execute('yum clean all')
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
            kc.copy_cache_or_repo(package, arch='noarch',
                                  ver=params.releaseversion,
                                  dir="KaveToolbox")
            Execute('tar -xzf ' + package)
            # try to cope with the annoying way the tarball contains something with .git at the end!
            import glob

            for gits in glob.glob(self.sttmpdir + "/*.git"):
                if os.path.isdir(gits) and not gits.endswith("/.git"):
                    Execute('mv ' + gits + ' ' + gits[:-len(".git")])
            instscript = './KaveToolbox/scripts/KaveInstall'
        Execute("mkdir -p /etc/kave")
        Execute('chmod -R a+r /etc/kave')
        File("/etc/kave/CustomInstall.py",
             content=InlineTemplate(params.custom_install_template),
             mode=0644
             )

        commandlineargs = ""
        if params.command_line_args:
            commandlineargs = " " + params.command_line_args

        noexec_detected = 0
        if 'noexec' in subprocess.check_output('if mountpoint -q /tmp; then mount | grep "/tmp "; fi', shell=True):
            noexec_detected = 1
            Execute("mount -o remount,exec /tmp")

        Execute(instscript + ' --' + self.kind + extraopts + commandlineargs,
                logoutput=True)
        os.chdir(topdir)
        Execute("rm -rf " + self.sttmpdir + "/*")
        Execute('touch /etc/kave/toolbox_ok')
        Execute('yum -y install --setopt=retries=20 --setopt=timeout=60 python-pip')
        Execute('bash -c "source /opt/KaveToolbox/pro/scripts/KaveEnv.sh ;pip install --upgrade pip"')
        Execute('bash -c "source /opt/KaveToolbox/pro/scripts/KaveEnv.sh ; pip install lightning-python"')
        File("/opt/KaveToolbox/pro/config/kave-env-exclude-users.conf",
             content=InlineTemplate(params.kave_env_excluded_users),
             mode=0644
             )
        File("/etc/profile.d/ktb_custom_env.sh",
             content=InlineTemplate(params.kave_custom_environment),
             mode=0644
             )
        # Restart salt minion service. Otherwise it fails because of some python package installs/upgrades required
        # by KaveToolbox
        salt_check = subprocess.Popen('systemctl is-active --quiet salt-minion.service', shell=True)
        salt_check.wait()
        if int(salt_check.returncode) == 0:
            Execute('systemctl restart salt-minion.service')
        if noexec_detected:
            Execute("mount -o remount,noexec /tmp")

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
        File("/etc/profile.d/ktb_custom_env.sh",
             content=InlineTemplate(params.kave_custom_environment),
             mode=0644
             )
        # On the first call (see func: install) this config does not exists.
        # Later if configuration is changed it should be present
        if os.path.exists('/opt/KaveToolbox/pro/config/kave-env-exclude-users.conf'):
            File("/opt/KaveToolbox/pro/config/kave-env-exclude-users.conf",
                 content=InlineTemplate(params.kave_env_excluded_users),
                 mode=0644
                 )
        Execute("chmod -R a+r /etc/kave")

    def status(self, env):
        with open(self.status_file, 'r') as content_file:
            content = content_file.read()
        if int(content) != 0:
            raise ComponentIsNotRunning()
        return True

    def start(self, env):
        Execute("echo 0 > " + self.status_file)

    def stop(self, env):
        Execute("echo 1 > " + self.status_file)

    def restart(self, env):
        self.stop(env)
        self.configure(env)
        self.start(env)

if __name__ == "__main__":
    KaveToolbox().execute()
