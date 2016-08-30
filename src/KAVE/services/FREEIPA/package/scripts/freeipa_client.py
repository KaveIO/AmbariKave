##############################################################################
#
# Copyright 2016 KPMG Advisory N.V. (unless otherwise stated)
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
import glob
import kavecommon as kc
from resource_management import *
from resource_management.core.exceptions import ComponentIsNotRunning


class FreeipaClient(Script):

    packages = ['ntp', 'curl', 'wget', 'pdsh', 'openssl', 'ipa-client',
                'ipa-admintools', 'oddjob-mkhomedir']
    ipa_client_install_lock_file = '/root/ipa_client_install_lock_file'

    def status(self, env):
        raise ClientComponentHasNoStatus()

    def write_resolvconf(self, env):
        """
        Common method to overwrite resolv.conf if required
        sensitive to the value of params.install_with_dns

        NB: If we are installing freeipa with DNS the settings in resolv.conf must
        be overriden. However these new settings will probably not survive a
        network restart. This could cause potential problems.

        This also can cause a lot of issues on failed FreeIPA installations, or while
        the FreeIPA server is switched off, and so we give the user full control over
        the resolv.conf template so that they can modify this approach if needed
        """
        import params
        env.set_params(params)
        if params.install_with_dns:
            File("/etc/resolv.conf",
                 content=InlineTemplate(params.resolvconf_template),
                 mode=0644
                 )

    def install(self, env):
        import params
        env.set_params(params)

        self.install_jce()
        installed_on_server = (params.ipa_server == params.hostname)

        if installed_on_server:
            print 'The FreeIPA client installation is modified when installed on the freeipa server:',
            print ' %s freeipa_server %s' % (params.ipa_server, params.hostname)

        if os.path.exists(self.ipa_client_install_lock_file):
            print 'ipa client already installed, nothing to do here.'
            return self.write_resolvconf(env)

        rm = freeipa.RobotAdmin()
        # Native package installation system driven by metainfo.xml intentionally
        # avoided. Both client and server components are very different and don't
        # intersect on any highlevel component.
        if not installed_on_server:
            for package in self.packages:
                Package(package)

            Execute('chkconfig ntpd on')

            # patch for long domain names!
            if params.long_domain_patch:
                Execute("grep -IlR 'Certificate Authority' /usr/lib/python2.6/site-packages/ipa* "
                        "| xargs sed -i 's/Certificate Authority/CA/g'")

            # installs ipa-client software
            rm.client_install(params.ipa_server, params.domain, params.client_init_wait, params.install_with_dns)

        # here we remove the robot-admin-password in case we are not running on the server
        # Note the strange construction due to the enter/exit clauses of the get_freeipa method
        # Although it may look like these lines do nothing, do not be fooled
        with rm.get_freeipa(not installed_on_server) as fi:
            pass

        # Only write the resolv.conf if the client installation was successful, otherwise I can get into biiig trouble!
        self.write_resolvconf(env)

        if not os.path.exists(self.ipa_client_install_lock_file):
            with open(self.ipa_client_install_lock_file, 'w') as f:
                f.write('')

    def install_jce(self):
        import params
        # cache this download so that this can be redistributed on restart of the service
        kc.copy_cache_or_repo("jce_policy-7.zip", cache_dir='/etc/kave/cache', arch="noarch")
        kc.copy_cache_or_repo("jce_policy-8.zip", cache_dir='/etc/kave/cache', arch="noarch")
        # need to think of some protection against recursive softlinks
        for javapath in params.searchpath.split(':'):
            # print "this is javaPath"+javapath
            if not len(javapath):
                continue
            # Does the top directory exist and is it a directory?
            if os.path.isdir(os.path.realpath(os.sep.join(javapath.split(os.sep)[:-1]))):
                for dir in glob.glob(javapath):
                    dir = os.path.realpath(dir)
                    if os.path.isdir(dir):
                        # print os.listdir(dir)
                        for folderpath in params.folderpath.split(':'):
                            if not os.path.isdir(dir + '/' + folderpath):
                                Execute('mkdir -p ' + dir + '/' + folderpath)
                            if '1.7' == self.java_version_installed(dir):
                                Execute('unzip -o -j -q jce_policy-7.zip -d ' + dir + '/' + folderpath)
                            else:
                                Execute('unzip -o -j -q jce_policy-8.zip -d ' + dir + '/' + folderpath)

    def java_version_installed(self, dir):
        if '1.7' in dir:
            return '1.7'
        else:
            return '1.8'

if __name__ == "__main__":
    FreeipaClient().execute()
