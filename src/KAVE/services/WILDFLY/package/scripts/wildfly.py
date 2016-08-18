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
import kavecommon as kc
from resource_management import *
import pwd
import grp
import os
from resource_management.core.exceptions import ComponentIsNotRunning


class Wildfly(Script):
    installer_cache_path = '/tmp/'
    package = 'wildfly-10.1.0.CR1.zip'
    symlink = '/var/lib/ambari-agent/tmp/wildfly'

    def install(self, env):
        import params

        env.set_params(params)
        self.install_packages(env)

        kc.copy_cache_or_repo(self.package, cache_dir=self.installer_cache_path, arch='noarch')
        self.clean_up_failed_install()
        Execute('unzip -o -q %s ' % (self.package))
        Execute('mv %s %s' % (self.package.replace('.zip', ''), params.installation_dir))
        # Execute('rm -rf %s/jb*.Final' % params.installation_dir)
        try:
            grp.getgrnam(params.service_user)
        except KeyError:
            Execute('groupadd ' + params.service_user)
        try:
            pwd.getpwnam(params.service_user)
        except KeyError:
            Execute('useradd -s /bin/bash -g %s %s' % (params.service_user, params.service_user))

        Execute('chown -Rf %s:%s %s' % (params.service_user, params.service_user, params.installation_dir))

        import glob
        if not len(glob.glob(params.JAVA_HOME)):
            raise ValueError("Could not find JAVA_HOME in location : " + params.JAVA_HOME)

        self.configure(env)

    def clean_up_failed_install(self):
        import params
        if os.path.exists(params.installation_dir):
            Execute('rm -rf %s' % params.installation_dir)

    def start(self, env):
        import params
        env.set_params(params)
        self.configure(env)
        Execute('nohup ' + params.bin_dir +
                '/standalone.sh < /dev/null '
                '>> %s/stdout >> %s/stderr &' % (params.log_dir, params.log_dir),
                wait_for_finish=False, user=params.service_user)
        if os.path.exists(self.symlink):
            Execute('rm -f ' + self.symlink)
        Execute('ln -s ' + params.installation_dir + ' ' + self.symlink)
        # write a file with the bind address and the port number for the management somewhere
        import time
        time.sleep(6)

    def stop(self, env):
        import params
        env.set_params(params)
        # use the bind address/port number!
        Execute('nohup ' + params.bin_dir
                + '/jboss-cli.sh --connect command=:shutdown '
                + '< /dev/null '
                + '>> %s/stdout >> %s/stderr &' % (params.log_dir, params.log_dir),
                wait_for_finish=False)

    def restart(self, env):
        import time
        self.stop()
        time.sleep(6)
        self.start()

    def status(self, env):
        # need to save pid in filr and retrieve to see the value of status
        import subprocess
        # use the bind address/port number!
        p = subprocess.Popen([self.symlink + '/bin/jboss-cli.sh',
                              '--connect',
                              'command=:read-attribute(name=server-state)'],
                             stdout=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if '"running"' not in stdout:
            print stdout, stderr
            raise ComponentIsNotRunning()

    def configure(self, env):
        import params

        env.set_params(params)
        if not os.path.exists(params.log_dir):
            Execute('mkdir -p ' + params.log_dir)
        Execute('chown -R %s:%s %s' % (params.service_user, params.service_user, params.log_dir))
        File(params.wildfly_conf_file,
             content=InlineTemplate(params.wildflyxmlconfig),
             mode=0644
             )

        if params.management_password:
            mgmt_users_file = ''
            with open(params.mgmt_users_file, "r") as input:
                mgmt_users_file = input.readlines()
            with open(params.mgmt_users_file, "w") as output:
                # Remove any old admin user if present
                for line in mgmt_users_file:
                    output.write(re.sub(r'^admin=.*$', '', line))
                # Append new admin user at the end of the file
                output.write("\nadmin=%s" % generate_password_hash(params.management_password))


def generate_password_hash(password, user='admin', realm='ManagementRealm'):
    import md5

    return md5.new('%s:%s:%s' % (user, realm, password)).hexdigest()


if __name__ == "__main__":
    Wildfly().execute()
