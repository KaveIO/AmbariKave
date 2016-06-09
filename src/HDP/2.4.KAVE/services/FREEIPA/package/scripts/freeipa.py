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
import subprocess
import os
import os.path
import time
import datetime
import random
import string
import pwd
import grp


def protect(apass):
    try:
        from resource_management import Logger
        Logger.sensitive_strings[apass] = "[PROTECTED]"
    except ImportError:
        return


class RobotAdmin():
    """ A helper class for delegating credentials and tasks to client nodes.

    The freeipa service faces some challenges in its reasoning about security.
    While it is the primary authority for authentication it is also managed by
    ambari. In order to avoid sending over the admin password for each client
    install some tricks had to be done. The RobotAdmin takes care of the
    orchestration of this.
    During the server install the RobotAdmin class is used to generate a
    special admin user with a random password and a limited lifetime. The
    password for this account is distributed over SSH to a protected file on all
    client nodes. This is done only once per client and a file is being
    maintained on the server to ensure this constraint.
    The client can login with this password exactly once through this class.
    After this the file is destroyed and the credentials lost. This single
    window of admin privileges should be used during the initial installation
    of the host through Ambari and should be used for installing the freeipa
    client, adding the neccesary service principals and fetching the keytabs for
    said principals.

    Attributes:
        login (str): username of the robot admin principal
        password_file (str): file in which the robot-admin password is stored
        previously_distributed_file (str): file which contains a list of machine
            names which received a password_file earlier
        ambari_db_password_file (str): path to the file which contains the
            password of the ambari database
    """

    login = 'robot-admin'
    password_file = '/root/%s-password' % login
    previously_distributed_file = '/root/%s-previously-distributed' % login
    ambari_db_password_file = '/etc/ambari-server/conf/password.dat'

    def get_login(self):
        return self.login

    def get_password_file(self):
        return self.password_file

    def get_freeipa(self, destroy_password_file=True):
        return FreeIPA(self.login, self.password_file, destroy_password_file)

    def distribute_password(self, all_hosts=None):
        previously_distributed_hosts = self._previously_distributed_hosts()
        if all_hosts is None:
            all_hosts = self._all_hosts()

        new_hosts = [host for host in all_hosts if host not in previously_distributed_hosts]

        for new_host in new_hosts:
            subprocess.call(['scp', '-o', 'StrictHostKeyChecking=no',
                             self.password_file, '%s:%s' % (new_host, self.password_file)])

        self._update_distributed_hosts(new_hosts)

    def client_install(self, server, domain, wait_limit=600, install_with_dns=True):
        start_time = datetime.datetime.now()

        while not os.path.exists(self.password_file) \
                and (datetime.datetime.now() - start_time).seconds < wait_limit:
            time.sleep(1)

        if os.path.isfile(self.password_file):

            options = ['--enable-dns-updates', '--ssh-trust-dns', '--domain', domain] if install_with_dns else []

            # Install the ipa-client software, This requires the robot-admin password.
            p1 = subprocess.Popen(['cat', self.password_file], stdout=subprocess.PIPE)
            p2 = subprocess.Popen(['ipa-client-install', '--mkhomedir',
                                   '--principal', self.login, '-W', '--server', server, '-U'] + options,
                                  stdin=p1.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p1.stdout.close()
            stdout, stderr = p2.communicate()
            if p2.returncode:
                raise OSError("Failed to install FreeIPA client!\n\t" + stdout + '\n\t' + stderr)
        else:
            raise Exception('No robot-admin password could be found in %s ' % self.password_file)

    def _previously_distributed_hosts(self):
        hosts = []
        try:
            with open(self.previously_distributed_file, 'r') as f:
                hosts = f.read().splitlines()
        finally:
            return hosts

    def _update_distributed_hosts(self, hosts):
        with open(self.previously_distributed_file, 'a') as f:
            for host in hosts:
                f.write(host + '\n')

    def _all_hosts(self):
        with open(self.ambari_db_password_file) as f:
            password = f.read()
            protect(password)
            env = os.environ.copy()
            env['PGPASSWORD'] = password

            # Fetch the list of all hosts with a FREEIPA_CLIENT hostcomponent
            # this call is a big part of the reason why freeipa is bound hard to
            # the ambari server.
            p = subprocess.Popen(['psql', 'ambari', 'ambari', '-q', '-A', '-t',
                                  '-c', 'select hosts.host_name from hosts join hostcomponentstate \
                on hostcomponentstate.host_id = hosts.host_id where \
                component_name = \'FREEIPA_CLIENT\';'], stdout=subprocess.PIPE,
                                 env=env)
            output, err = p.communicate()
            hosts = filter(bool, output.split("\n"))
            if len(hosts):
                print "hosts found from ambari database scraping"
            return hosts


class FreeIPACommon(object):
    """
    Many of the methods we want to call within FreeIPA are common
    We can make a baseclass/Mix-ins class here in order to simplify/consolidate other scripts
    """

    def create_user_principal(self, identity, firstname=None,
                              lastname='auto_generated', groups=[],
                              password=None, password_file=None):
        if not self.user_exists(identity):
            if firstname is None:
                firstname = identity
            subprocess.call(['ipa', 'user-add', '--first', firstname, '--last', lastname, identity])

            for group in groups:
                self.group_add_member(group, identity)

            if password is not None:
                protect(password)
                self.update_password(identity, password, password_file)
        else:
            print 'Skipping user creation for %s. User already exists' % identity

    def create_sudorule(self, rulename, **kwargs):
        """
        kwargs Users: users to add to the rule
        kwargs Groups: groups to add to the rule
        All other kwargs are passed as command line parameters --key=val
        """
        if not self.sudorule_exists(rulename):
            cmd = ['ipa', 'sudorule-add', rulename] + ['--' + k + '=' + v for k,
                                                       v in kwargs.iteritems() if k != "Users" and k != "Groups"]
            subprocess.call(cmd)
            if "Users" in kwargs and len(kwargs["Users"]):
                subprocess.call(['ipa', 'sudorule-add-user', '--users=' + ','.join(kwargs["Users"]), rulename])
            if "Groups" in kwargs and len(kwargs["Groups"]):
                subprocess.call(['ipa', 'sudorule-add-user', '--groups=' + ','.join(kwargs["Groups"]), rulename])
        else:
            print 'Skipping user creation for %s. Rule already exists' % rulename

    def create_service_principal(self, principal):
        if not self.service_exists(principal):
            subprocess.call(['ipa', 'service-add', principal])

    def create_group(self, group, description, options=[]):
        if not self.group_exists(group):
            subprocess.call(['ipa', 'group-add', group, '--desc', description] + options)

    def create_keytab(self, server, principal, realm, file, user, group, permissions):
        if not os.path.isdir(os.path.dirname(file)):
            os.mkdir(os.path.dirname(file), 0555)

        full_principal = '%s@%s' % (principal, realm)
        subprocess.call(['ipa-getkeytab', '-s', server, '-p', full_principal, '-k', file])

        ownership = '%s:%s' % (user, group)
        subprocess.call(['chown', ownership, file])
        subprocess.call(['chmod', permissions, file])

    def user_exists(self, user):
        try:
            with open(os.devnull, "w") as devnull:
                subprocess.check_call(['ipa', 'user-show', user], stderr=devnull)
            return True
        except:
            pass
        return False

    def sudorule_exists(self, sudorule):
        try:
            with open(os.devnull, "w") as devnull:
                subprocess.check_call(['ipa', 'sudorule-show', sudorule], stderr=devnull)
            return True
        except:
            pass
        return False

    def service_exists(self, service):
        try:
            with open(os.devnull, "w") as devnull:
                subprocess.check_call(['ipa', 'service-show', service], stderr=devnull)
            return True
        except:
            pass
        return False

    def group_exists(self, group):
        try:
            with open(os.devnull, "w") as devnull:
                subprocess.check_call(['ipa', 'group-show', group], stderr=devnull)
            return True
        except:
            pass
        return False

    def group_add_member(self, group, user):
        subprocess.call(['ipa', 'group-add-member', group, '--users=%s' % user])

    def update_password(self, user, password, password_file=None):
        if password_file is None:
            password_file = '/root/%s-password' % user

        with os.fdopen(os.open(password_file, os.O_WRONLY | os.O_CREAT, 0600), 'w') as handle:
            protect(password)
            handle.write(password)

        p1 = subprocess.Popen(['cat', password_file], stdout=subprocess.PIPE)
        p2 = subprocess.Popen(['ipa', 'user-mod', user, '--password'], stdin=p1.stdout)
        p1.stdout.close()
        p2.communicate()

    def set_default_shell(self, shell):
        subprocess.call(['ipa', 'config-mod', '--defaultshell=' + shell])

    def set_user_email(self, user, email):
        subprocess.call(['ipa', 'user-mod', '--email', email, user])


class FreeIPA(FreeIPACommon):
    """
    The FreeIPA Object is supposed to be used with the python "with" statement
    This object calls kinit from a local password file, and then can destroy that file when done with it.
    Otherwise inherits all the methods from the FreeIPACommon class
    """

    def __init__(self, principal, password_file, destroy_password_file=True):
        self.principal = principal
        self.password_file = password_file
        self.destroy_password_file = destroy_password_file

    def __enter__(self):
        with open(os.devnull, "w") as devnull:
            p1 = subprocess.Popen(['cat', self.password_file], stdout=subprocess.PIPE)
            p2 = subprocess.Popen(['kinit', self.principal], stdin=p1.stdout, stdout=devnull)
            p1.stdout.close()
            p2.communicate()

        if self.destroy_password_file:
            os.remove(self.password_file)

        return self

    def __exit__(self, type, value, trace):
        subprocess.call(['kdestroy'])


def generate_random_password(length=16):
    """
    Helper function for generating a random password.

    Arguments:
        length (int): How many characters the password contains
    """
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(length))


def create_required_users(required_users):
    """
    Helper function for creating native linux users and groups.

    In order to make the entire freeipa thing work there need to be some special
    users already be present on the system. These can be added through this
    function.

    Arguments:
        required_users (object): object containing the users to add.
    """
    for user, details in required_users.iteritems():
        groups = details['groups'] if ('groups' in details) else []
        comment = details['comment'] if ('comment' in details) else ''
        options = details['options'] if ('options' in details) else []

        create_user(user, groups, comment, options)


def create_group(group):
    """
    Helper function for creating native linux group.

    Checks if the group already exists. If it doesn't the requested group is
    created.

    Arguments:
        group (string): name of the group to create
    """
    try:
        grp.getgrnam(group)
    except KeyError:
        subprocess.call(['groupadd', group])


def create_user(user, groups=[], comment='', options=[]):
    """
    Helper function for creating a native linux user and its required groups.

    First tries to create all the required groups. Once done the user will be
    created and added to the group.

    Arguments:
        user (string): name of the user to create
        groups (list): if empty user will be added to its own group, if only
            one entry this will be used as the users primary group, if multiple
            entries the first entry will be the primary group and the rest
            additional groups.
    """
    for group in groups:
        create_group(group)
    try:
        pwd.getpwnam(user)
    except KeyError:
        if len(comment):
            options.extend(['-c', comment])

        if len(groups) == 0:
            subprocess.call(['useradd'] + options + [user])
        elif len(groups) == 1:
            subprocess.call(['useradd', '-g', groups[0]] + options + [user])
        else:
            subprocess.call(['useradd', '-g', groups[0], '-G', ','.join(groups[1:])] + options + [user])
