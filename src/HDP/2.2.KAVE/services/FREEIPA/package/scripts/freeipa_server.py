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
import freeipa
import os
import datetime

from resource_management import *


class FreeipaServer(Script):
    admin_login = 'admin'
    admin_password_file = '/root/admin-password'
    packages = ['ipa-server', 'bind', 'bind-dyndb-ldap']

    def install(self, env):
        import params
        self.install_packages(env)
        env.set_params(params)

        if params.ipa_server != params.hostname:
            raise Exception('The FreeIPA server installation has a hard requirement to be installed'
                            ' on the ambari server. ambari_server: %s freeipa_server %s'
                            % (params.ipa_server, params.hostname))

        freeipa.create_required_users(params.required_users)

        for package in self.packages:
            Package(package)

        admin_password = freeipa.generate_random_password()

        # ipa-server install command. Currently --selfsign is mandatory because
        # of some anoying centos6.5 problems. The underling installer uses an
        # outdated method for the dogtag system which fails.
        install_command = 'ipa-server-install -U  --selfsign --realm="%s" \
            --ds-password="%s" --admin-password="%s"' \
            % (params.realm, params.directory_password, admin_password)

        if params.forwarders:
            for forwarder in params.forwarders:
                install_command += ' --forwarder="%s"' % forwarder
        else:
            install_command += ' --no-forwarders'

        if params.install_with_dns:
            install_command += ' --setup-dns --domain="%s"' % params.domain

        # Crude check to avoid reinstalling during debuging
        if not os.path.exists(self.admin_password_file):
            # TODO avoid execute, this displays the admin passwords in the logs
            # which is bad m'kay
            Execute(install_command)

            File("/root/admin-password",
                 content=Template("admin-password.j2", admin_password=admin_password),
                 mode=0600
                 )
        # set the default shell
        with freeipa.FreeIPA(self.admin_login, self.admin_password_file, False) as fi:
            fi.set_default_shell(params.default_shell)
        self.create_base_accounts(env)
        # create initial users and groups
        with freeipa.FreeIPA(self.admin_login, self.admin_password_file, False) as fi:

            if "Users" in params.initial_users_and_groups:
                for user in params.initial_users_and_groups["Users"]:
                    if type(user) is str or type(user) is not dict:
                        user = {"username": user}
                    username = user["username"]
                    password = None
                    if username in params.initial_user_passwords:
                        password = params.initial_user_passwords[username]
                    firstname = username
                    lastname = 'auto_generated'
                    if 'firstname' in user:
                        firstname = user['firstname']
                    if 'lastname' in user:
                        lastname = user['lastname']
                    fi.create_user_principal(identity=username, firstname=firstname,
                                             lastname=lastname, password=password)
                    if "email" in user:
                        fi.set_user_email(username, user["email"])
            if "Groups" in params.initial_users_and_groups:
                groups = params.initial_users_and_groups["Groups"]
                if type(groups) is dict:
                    groups = [{"name": gname, "members": groups[gname]} for gname in groups]
                for group in groups:
                    freeipa.create_group(group["name"])
                    for user in group["members"]:
                        fi.group_add_member(group["name"], user)
            fi.create_sudorule('allsudo', **(params.initial_sudoers))
        # create robot admin
        self.reset_robot_admin_expire_date(env)
        self.distribute_robot_admin_credentials(env)

    def start(self, env):
        Execute('service ipa start')

    def stop(self, env):
        Execute('service ipa stop')

    def status(self, env):
        # Pretty weird call here. We need to enforce that the keys are
        # distributed to all agents when they are first installed. This proved
        # to be tricky to achieve in Ambari. This call distributes the
        # credentials to new hosts on each status heartbeat. Pretty weird but
        # for now it serves its purpose.
        self.distribute_robot_admin_credentials(env)

        Execute('service ipa status')

    def create_base_accounts(self, env):
        import params

        rm = freeipa.RobotAdmin()

        with freeipa.FreeIPA(self.admin_login, self.admin_password_file, False) as fi:
            fi.create_user_principal(
                rm.get_login(),
                groups=['admins'],
                password=freeipa.generate_random_password(),
                password_file=rm.get_password_file())

            for definition in params.headless_users.itervalues():
                fi.create_user_principal(definition['identity'])
                fi.create_keytab(
                    params.ipa_server,
                    definition['identity'],
                    params.realm,
                    definition['file'],
                    definition['user'],
                    definition['group'],
                    definition['permissions'])

            # Create ldap bind user
            expiry_date = (datetime.datetime.now() + datetime.timedelta(weeks=52 * 10)).strftime('%Y%m%d%H%M%SZ')
            File("/tmp/bind_user.ldif",
                 content=Template("bind_user.ldif.j2", expiry_date=expiry_date),
                 mode=0600
                 )
            import kavecommon as kc
            _stat, _stdout, _stderr = kc.mycmd(
                'ldapsearch -x -D "cn=directory manager" -w %s "uid=%s"'
                % (params.directory_password, params.ldap_bind_user))
            # is this user already added?
            if "dn: uid=" + params.ldap_bind_user not in _stdout:
                Execute('ldapadd -x -D "cn=directory manager" -w %s -f /tmp/bind_user.ldif'
                        % params.directory_password)
            for group in params.ldap_bind_services:
                fi.create_group(group, group + ' user group', ['--nonposix'])

    def reset_robot_admin_expire_date(self, env):
        import params
        env.set_params(params)

        rm = freeipa.RobotAdmin()
        expiry_date = (datetime.datetime.now() + datetime.timedelta(weeks=52)).strftime('%Y%m%d%H%M%SZ')
        File("/tmp/expire_date.ldif",
             content=Template("expire_date.ldif.j2",
                              login=rm.get_login(),
                              expiry_date=expiry_date),
             mode=0600
             )
        Execute('ldapadd -x -D "cn=directory manager" -w %s -f /tmp/expire_date.ldif' % params.directory_password)

    def distribute_robot_admin_credentials(self, env):
        rm = freeipa.RobotAdmin()
        rm.distribute_password()

if __name__ == "__main__":
    FreeipaServer().execute()
