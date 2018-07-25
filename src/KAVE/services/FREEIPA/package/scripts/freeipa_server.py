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
import freeipa
import os
import datetime
import subprocess

from resource_management import *


class FreeipaServer(Script):
    admin_login = 'admin'
    admin_password_file = '/root/admin-password'
    packages = ['ipa-server', 'bind', 'bind-dyndb-ldap']
    expected_services = ['chronyd', 'ntpd', 'ns-slapd']

    def checkport(self, number):
        """
        Certain ports must be free
        """
        import kavecommon as kc
        import time
        check = kc.check_port(number)
        # Proto Recv-Q Send-Q, Local Address, Foreign Address, State, User, Inode, PID/Program name

        if check is not None:
            if check[-4] == "TIME_WAIT":
                time.sleep(30)
                check = kc.check_port(number)

        def noprog(check):
            return (len(check) < 9 or check[-1] is None or '/' not in check[-1] or '?' in check[-1])

        if check is not None:
            if noprog(check):
                # this could be a temporary process
                time.sleep(1)
                check = kc.check_port(number)
        err = ''
        if check is not None:
            err = ("The port number %s is already in use on this machine. You must reconfigure FreeIPA ports"
                   " or install FreeIPA on a different node of your cluster. "
                   "\n\t (protocol, rq, sq, laddr, raddr, status, user, inode, pid/prog) \n\t %s "
                   % (number, check.__str__())
                   )
            # add process info if accessible
            if not noprog(check):
                p = kc.ps(check[-1].split('/')[0])
                err = err + ("\n\t [UID, PID, PPID, C, STIME, TTY, STAT, TIME, CMD] \n\t %s"
                             % (p.__str__())
                             )
                if check[-1].split('/')[-1] in self.expected_services:
                    err = ''
            if len(err):
                raise OSError(err)

    def install(self, env):
        import params
        env.set_params(params)

        # Execute('/etc/init.d/ambari-server stop')
        # Execute('yum -y remove ambari-server')

        p0 = subprocess.Popen(["hostname", "-f"], stdout=subprocess.PIPE)
        _hostname = p0.communicate()[0].strip()
        if p0.returncode:
            raise OSError("Failed to determine hostname!")

        import kavecommon as kc
        tos = kc.detect_linux_version()
        # Check that all known FreeIPA ports are available
        needed_ports = [88, 123, 389, 464, 636, 8080, 8443]
        for port in needed_ports:
            self.checkport(port)

        self.install_packages(env)

        for package in self.packages:
            Package(package)

        admin_password = freeipa.generate_random_password()
        Logger.sensitive_strings[admin_password] = "[PROTECTED]"

        # This should not be needed but somehow something reverts the v6 enable recipe.
        Execute("sysctl -w net.ipv6.conf.lo.disable_ipv6=0; ifconfig | grep -q ::1; if [ $? = 1 ]; "
                "then ifconfig lo inet6 add ::1; fi")

        # Try to reload dbus configuration due to a bug in dbus
        Execute("systemctl stop dbus")
        Execute("systemctl start dbus")

        install_command = 'ipa-server-install -U  --realm="%s" \
            --ds-password="%s" --admin-password="%s" --hostname="%s"' \
            % (params.realm, params.directory_password, admin_password, _hostname)

        # ipa-server install command. Currently --selfsign is mandatory because
        # of some anoying centos6.5 problems. The underling installer uses an
        # outdated method for the dogtag system which fails.
        # however, on centos7, this option does not exist!

        if params.install_with_dns:
            if tos.lower() in ["centos7"]:
                Package("ipa-server-dns")
            install_command += ' --setup-dns --domain="%s"' % params.domain

            # install_command += ' --setup-dns --domain=freeipa.kave.io'

            if params.forwarders:
                for forwarder in params.forwarders:
                    install_command += ' --forwarder="%s"' % forwarder
            else:
                install_command += ' --no-forwarders'

        p0 = subprocess.Popen(["ipactl", "status"], stdout=subprocess.PIPE)
        p0.communicate()
        ipacheck = p0.returncode
        if ipacheck == 4 or ipacheck == 127:

            # This is a time-consuming command, better to log the output
            Execute(install_command, logoutput=True)
            # write password file
            File("/root/admin-password",
                 content=Template("admin-password.j2", admin_password=admin_password),
                 mode=0600
                 )
        # Ensure service is started before trying to interact with it!
        Execute('systemctl start ipa')

        with freeipa.FreeIPA(self.admin_login, self.admin_password_file, False) as fi:
            # set the default shell
            fi.set_default_shell(params.default_shell)
            # Set the admin user shell
            fi.set_user_shell(self.admin_login, params.admin_user_shell)
            # make base accounts
            self.create_base_accounts(env, fi)

            # create initial users and groups
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
        # Enable security options for Apache
        with open("/etc/httpd/conf/httpd.conf", "a") as httpd_conf:
            httpd_conf.write("TraceEnable Off\nServerSignature Off\nServerTokens Prod")
        Execute('systemctl restart httpd')
        # if FreeIPA server is not started properly, then the clients will not install
        self.start(env)

    def conf_on_start(self, env):
        import params
        env.set_params(params)
        File("/var/kerberos/krb5kdc/kadm5.acl",
             content=InlineTemplate(params.kadm5acl_template),
             mode=0600
             )
        File("/root/createkeytabs.py",
             content=Template("createkeytabs.py", scriptpath=os.path.dirname(__file__)),
             mode=0700
             )

    def start(self, env):
        self.conf_on_start(env)
        self.distribute_robot_admin_credentials(env)
        Execute('systemctl start ipa')

    def stop(self, env):
        Execute('systemctl stop ipa')

    def restart(self, env):
        Execute('systemctl restart ipa')

    def status(self, env):
        # Pretty weird call here. We need to enforce that the keys are
        # distributed to all agents when they are first installed. This proved
        # to be tricky to achieve in Ambari. This call distributes the
        # credentials to new hosts on each status heartbeat. Pretty weird but
        # for now it serves its purpose.
        try:
            self.distribute_robot_admin_credentials(env)
        except (subprocess.CalledProcessError, OSError, TypeError, ImportError, ValueError, KeyError) as e:
            print "Failed to distribute robot credentials during status call: known exception type"
            print e, type(e)
            print sys.exc_info()
        except Exception as e:
            print "Failed to distribute robot credentials during status call: unknown exception type"
            print e, type(e)
            print sys.exc_info()

        check = subprocess.Popen('systemctl status ipa', shell=True)
        check.wait()
        if int(check.returncode) != 0:
            raise ComponentIsNotRunning()
        return True

    def create_base_accounts(self, env, fi):
        """
        fi: a FreeIPA object
        """
        import params

        rm = freeipa.RobotAdmin()

        fi.create_user_principal(
            rm.get_login(),
            groups=['admins'],
            password=freeipa.generate_random_password(),
            password_file=rm.get_password_file())

        fi.set_user_shell(rm.get_login(), params.admin_user_shell)
        # Always create the hadoop group
        fi.create_group('hadoop', 'the hadoop user group')

        # Create ldap bind user
        expiry_date = (datetime.datetime.now() + datetime.timedelta(weeks=52 * 10)).strftime('%Y%m%d%H%M%SZ')
        File("/tmp/bind_user.ldif",
             content=Template("bind_user.ldif.j2", expiry_date=expiry_date),
             mode=0600
             )
        import kavecommon as kc
        _stat, _stdout, _stderr = kc.shell_call_wrapper(
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
        # If this method is called during status, params will not
        # be available, and therefore I will need to read all_hosts
        # from the database instead
        # trying to import params could result in many possible issues here,
        # most commonly ImportError or KeyError
        try:
            import params
            env.set_params(params)
            all_hosts = params.all_hosts
            user = params.install_distribution_user
            print "using params for all_hosts"
        except (TypeError, ImportError, ValueError, KeyError):
            all_hosts = None

        rm = freeipa.RobotAdmin()
        print "distribution to all hosts with host being", all_hosts
        rm.distribute_password(all_hosts=all_hosts, user=user)

if __name__ == "__main__":
    FreeipaServer().execute()
