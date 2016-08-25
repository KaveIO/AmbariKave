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

from resource_management import *
import kavecommon as kc


class Nagios(Script):
    nagios_conf_file = "/etc/httpd/conf.d/nagios.conf"
    nagios_contacts_file = "/etc/nagios/objects/contacts.cfg"
    nagios_passwd_dir = "/etc/nagios/passwd"

    def install(self, env):
        import params
        env.set_params(params)
        Execute('yum repolist')
        Execute('yum install nagios*')
        self.install_packages(env)
        self.configure(env)

    def configure(self, env):
        import params
        import kavecommon as kc

        env.set_params(params)
        File(self.nagios_conf_file,
             content=InlineTemplate(params.nagios_conf_file),
             mode=0755
             )
        File(self.nagios_contacts_file,
             content=InlineTemplate(params.nagios_contacts_file),
             mode=0755
             )

        Execute('service httpd start')
        Execute('chkconfig httpd on')
        #SET NAGIOS ADMINPASSWORD
        p = subprocess.Popen(['htpasswd' + self.nagios_passwd_dir + 'nagiosadmin'],
                             stdout=subprocess.PIPE, shell=True)
        stdout, stderr = p.communicate(str(params.nagios_admin_password) + '\n' +str(params.nagios_admin_password))
        if p.returncode or 'success' not in stdout:
                raise Exception('Unable create nagios admin password, did you enter wrong password second time?')

    def start(self, env):
        import params
        self.configure(env)
        Execute('service nagios start')

    def stop(self, env):
        Execute("service nagios stop")

    def status(self, env):
        print Execute("service nagios status")


if __name__ == "__main__":
    Nagios().execute()
