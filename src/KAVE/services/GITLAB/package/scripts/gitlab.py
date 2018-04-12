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
import shutil

from resource_management import *
from subprocess import Popen, PIPE, STDOUT


class Gitlab(Script):
    package = 'gitlab-ce-8.7.1-ce.1.%s.x86_64.rpm'
    installer_cache_path = '/tmp/'

    def install(self, env):
        # TODO: instead of throwing an exception here, I should enter gitlabs into the existing postgre database
        # correctly
        if os.path.exists('/var/lib/pgsql/data/pg_hba.conf'):
            raise SystemError(
                "You appear to already have a default postgre database installed (probably you're trying to put "
                "Gitlabs on the same machine as Ambari). This type of operation is not implemented yet.")
        import params
        # intelligently choose architecture
        import kavecommon as kc
        el = {"centos7": "el7"}
        self.package = self.package % el[kc.detect_linux_version().lower()]
        self.install_packages(env)
        env.set_params(params)

        kc.copy_cache_or_repo(self.package, cache_dir=self.installer_cache_path)
        # reset the password with set_password method
        # cretae SSL certificate
        Execute('rpm --replacepkgs -i %s' % self.package)
        Execute('mkdir -p /etc/gitlab/ssl/')
        country = "NA"
        state = "NA"
        locality = "NA"
        organization = "NA"
        organizationalun = "NA"
        commonname = params.hostname
        email = "gitlab@example.com"
        Execute(str.format('openssl req -x509 -nodes -days 3650 -newkey rsa:2048' +
                           ' -keyout /etc/gitlab/ssl/' + params.hostname + '.key -out /etc/gitlab/ssl/' + params.hostname + '.crt ' +
                           '-subj "/C={}/ST={}/L={}/O={}/OU={}/CN={}/emailAddress={}' +
                           '"', country, state, locality, organization, organizationalun, commonname, email))
        self.configure(env)
        self.set_password(env)

    def start(self, env):
        self.configure(env)
        Execute('gitlab-ctl start')

    def stop(self, env):
        Execute('gitlab-ctl stop')

    # method to set admin password
    def set_password(self, env):
        import params
        env.set_params(params)
        admin_password = params.gitlab_admin_password
        slave = Popen(['gitlab-rails', 'console'], stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        # setting the admin password and printing the details on console
        slave.stdin.write('u = User.where(id:1).first\n')
        slave.stdin.write('u.password = \'%s\'\n' % admin_password)
        slave.stdin.write('u.password_confirmation = \'%s\'\n' % admin_password)
        slave.stdin.write('u.save!\n')
        out, err = slave.communicate()
        print out

    def configure(self, env):
        import params

        env.set_params(params)

        File(params.gitlab_conf_file,
             content=InlineTemplate(params.gitlabrb),
             mode=0600
             )

        Execute('gitlab-ctl start postgresql')
        Execute('gitlab-ctl reconfigure')

    def status(self, env):
        check = Popen('gitlab-ctl status', shell=True)
        check.wait()
        if int(check.returncode) != 0:
           raise ComponentIsNotRunning()
        return True

    def restart(self, env):
        self.configure(env)
        Execute('gitlab-ctl restart')

if __name__ == "__main__":
    Gitlab().execute()
