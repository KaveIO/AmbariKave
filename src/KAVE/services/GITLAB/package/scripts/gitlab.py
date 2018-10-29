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

from resource_management import *
from subprocess import Popen, PIPE, STDOUT


class Gitlab(Script):
    package = 'gitlab-ce-8.7.1-ce.1.%s.x86_64.rpm'
    installer_cache_path = '/tmp/'

    def install(self, env):
        import params
        # intelligently choose architecture
        import kavecommon as kc
        el = {"centos7": "el7"}
        self.package = self.package % el[kc.detect_linux_version().lower()]
        self.install_packages(env)
        env.set_params(params)

        kc.copy_cache_or_repo(self.package, cache_dir=self.installer_cache_path)

        if params.use_external_postgres:
            Execute('sudo -u postgres psql -d template1 -c "CREATE USER ' + str(params.postgres_database_user) +
                    ' WITH PASSWORD \'%s\';"' % params.gitlab_admin_password)
            Execute('sudo -u postgres psql -d template1 -c "ALTER USER %s CREATEDB;"' % params.postgres_database_user)
            Execute('sudo -u postgres psql -d template1 -c ' +
                    '"CREATE DATABASE {} OWNER {};"'.format(params.postgres_database_name,
                                                            params.postgres_database_user))
            Execute('sudo -u postgres psql -d template1 -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"')

        # reset the password with set_password method
        # cretae SSL certificate
        Execute('rpm --replacepkgs -i %s' % self.package)

        if params.use_external_postgres:
            Execute('gitlab-ctl reconfigure')
            Execute('gitlab-rake gitlab:setup force=yes')
        Execute('mkdir -p /etc/gitlab/ssl/')
        country = "NA"
        state = "NA"
        locality = "NA"
        organization = "NA"
        organizationalun = "NA"
        if len(params.hostname) <= 64:
            commonname = params.hostname
        else:
            commonname = params.hostname.split(".", 1)[0]
        email = "gitlab@example.com"
        Execute(str.format('openssl req -x509 -nodes -days 3650 -newkey rsa:2048' +
                           ' -keyout /etc/gitlab/ssl/' + str(params.hostname) + '.key -out ' +
                           '/etc/gitlab/ssl/' + str(params.hostname) + '.crt ' +
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
