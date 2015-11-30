##############################################################################
#
# Copyright 2015 KPMG N.V. (unless otherwise stated)
#
#   Licensed under the Apache License, Version 2.0 (the "License");
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
import freeipa
import os

from resource_management import *
from resource_management.core.exceptions import ComponentIsNotRunning

class FreeipaClient(Script):

    packages = ['ntp', 'curl', 'wget', 'pdsh', 'openssl', 'ipa-client',
                'ipa-admintools', 'oddjob-mkhomedir']
    ipa_client_install_lock_file = '/root/ipa_client_install_lock_file'

    def status(self,env):
        if not os.path.exists(self.ipa_client_install_lock_file):
            raise ComponentIsNotRunning()

    def install(self, env):
        import params
        env.set_params(params)
        installed_on_server = (params.ipa_server == params.hostname)

        if installed_on_server:
            print 'The FreeIPA client installation is modified when installed on the freeipa server:',
            print ' %s freeipa_server %s' % (params.ipa_server, params.hostname)

        # If we are installing freeipa with DNS the settings in resolv.conf must
        # be overriden. However these new settings wil probably not survive a
        # network restart. This could cause potential problems.
        if params.install_with_dns:
                File("/etc/resolv.conf",
                     content=InlineTemplate(params.resolvconf_template),
                     mode=0644
                     )

        if not os.path.exists(self.ipa_client_install_lock_file):
            with open(self.ipa_client_install_lock_file, 'w') as f:
                f.write('')
        else:
            print 'ipa client already installed, nothing to do here.'
            return

        freeipa.create_required_users(params.required_users)

        rm = freeipa.RobotAdmin()
        # Native package installation system driven by metainfo.xml intentionally
        # avoided. Both client and server components are very different and don't
        # intersect on any highlevel component.
        if not installed_on_server:
            for package in self.packages:
                Package(package)

            Execute('chkconfig ntpd on')

            # installs ipa-client software
            rm.client_install(params.ipa_server, params.domain, params.client_init_wait, params.install_with_dns)

        with rm.get_freeipa(not installed_on_server) as fi:

            for definition in params.service_users.itervalues():
                if params.hostname in definition['hosts']:
                    principal = '%s/%s' % (definition['identity'], params.hostname)
                    fi.create_service_principal(principal)
                    fi.create_keytab(
                        params.ipa_server,
                        principal,
                        params.realm,
                        definition['file'],
                        definition['user'],
                        definition['group'],
                        definition['permissions'])

            for definition in params.headless_users.itervalues():
                fi.create_keytab(
                    params.ipa_server,
                    definition['identity'],
                    params.realm,
                    definition['file'],
                    definition['user'],
                    definition['group'],
                    definition['permissions'])

if __name__ == "__main__":
    FreeipaClient().execute()
