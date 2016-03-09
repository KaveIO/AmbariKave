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
import kavecommon as kc
from resource_management import *
import pwd
import grp


class Jboss(Script):
    installer_cache_path = '/tmp/'
    package = 'jboss-as-7.1.1.Final.zip'

    def install(self, env):
        import params

        env.set_params(params)
        self.install_packages(env)

        kc.copyCacheOrRepo(self.package, cache_dir=self.installer_cache_path)
        Execute('unzip -o -q %s -d %s' % (self.package, params.installation_dir))
        Execute('mv %s/jb*/* %s' % (params.installation_dir, params.installation_dir))
        Execute('rm -rf %s/jb*.Final' % params.installation_dir)
        try:
            grp.getgrnam('jboss')
        except KeyError:
            Execute('groupadd jboss')
        try:
            pwd.getpwnam('jboss')
        except KeyError:
            Execute('useradd -s /bin/bash -g jboss jboss')

        Execute('chown -Rf jboss:jboss %s' % params.installation_dir)

        File('/etc/init.d/jboss',
             content=Template("jboss.j2"),
             mode=0755
             )

        Execute('chkconfig --add jboss')
        Execute('chkconfig --level 234 jboss on')

        self.configure(env)

    def start(self, env):
        # @fixme The jboss start doesn't return nicely if the output is not catched.
        # So the > /dev/null fixes this. However this not really a fundamental
        # solution
        self.configure(env)
        Execute('service jboss start > /dev/null')

    def stop(self, env):
        Execute('service jboss stop')

    def restart(self, env):
        self.configure(env)
        Execute('service jboss restart > /dev/null')

    def status(self, env):
        Execute('service jboss status')

    def configure(self, env):
        import params

        env.set_params(params)

        File(params.jboss_conf_file,
             content=InlineTemplate(params.jbossconfig),
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
    Jboss().execute()
