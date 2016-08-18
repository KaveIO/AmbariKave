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


class Wildfly(Script):
    installer_cache_path = '/tmp/'
    package = 'wildfly-10.1.0.CR1.zip'

    def install(self, env):
        import params

        env.set_params(params)
        self.install_packages(env)

        kc.copy_cache_or_repo(self.package, cache_dir=self.installer_cache_path, arch='noarch')
        self.clean_up_failed_install()
        Execute('unzip -o -q %s -d %s' % (self.package, params.installation_dir))
        Execute('mv %s/jb*/* %s' % (params.installation_dir, params.installation_dir))
        Execute('rm -rf %s/jb*.Final' % params.installation_dir)
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

        Execute('chkconfig --add wildfly')
        Execute('chkconfig wildfly on')

        self.configure(env)

    def clean_up_failed_install(self):
        import params
        if os.path.exists(params.installation_dir):
            Execute('rm -rf %s' % params.installation_dir)

    def start(self, env):
        # @fixme The jboss start doesn't return nicely if the output is not catched.
        # So the > /dev/null fixes this. However this not really a fundamental
        # solution
        self.configure(env)
        Execute('nohup'+ params.bin_dir + './standalone.sh > /var/log/wildfly/stdin > /var/log/wildfly/stdout > /var/log/wildfly/error &',wait_for_finish=False)

    def stop(self, env):
        Execute('nohup' +params.bin_dir +'./jboss-cli.sh --connect command=:shutdown > /var/log/wildfly/stdin > /var/log/wildfly/stdout > /var/log/wildfly/error &',wait_for_finish=False )


    def restart(self, env):
        self.configure(env)
        #Execute('service wildfly restart > /dev/null')

    def status(self, env):
        #need to save pid in filr and retrieve to see the value of status
        Execute('service wildfly status')

    def configure(self, env):
        import params

        env.set_params(params)

        File(params.jboss_conf_file,
             content=InlineTemplate(params.jbossxmlconfig),
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
