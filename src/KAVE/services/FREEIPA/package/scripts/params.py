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
import re
import socket
import json
import kavecommon as kc
import subprocess

from resource_management import *

config = Script.get_config()

hostname = config["hostname"]

amb_server = default("/clusterHostInfo/ambari_server_host", [False])[0]

ipa_server = default("/clusterHostInfo/freeipa_server_hosts", [False])[0]

if not ipa_server:
    raise KeyError('ipa_server could not be found in this cluster, this is strange and indicates much worse problems'
                   ' FreeIPA Client is the client partner of the server, so cannot install without its mommy')

ipa_domain = default('configurations/freeipa/ipa_domain', 'cloud.kave.io')
if not ipa_domain:
    raise Exception('ipa_domain appears to be empty')

ipa_server_ip_address = socket.gethostbyname(ipa_server)
if not ipa_server_ip_address:
    raise Exception('ipa_server_ip_address couldn\'t be determined')

directory_password = default('configurations/freeipa/directory_password', False)
if not directory_password or len(directory_password) < 8:
    raise Exception('FreeIPA directory_password: \'%s\' isn\'t acceptable (min 8 char long)' % directory_password)
else:
    Logger.sensitive_strings[directory_password] = "[PROTECTED]"

ldap_bind_password = default('configurations/freeipa/ldap_bind_password', False)
if not ldap_bind_password or len(ldap_bind_password) < 8:
    raise Exception('FreeIPA ldap_bind_password: \'%s\' isn\'t acceptable (min 8 char long)' % ldap_bind_password)
else:
    Logger.sensitive_strings[ldap_bind_password] = "[PROTECTED]"

domain_components = ipa_domain.split('.')
if len(domain_components) < 2:
    raise Exception('FreeIPA domain is not a FQDN. installation not possible')

domain = ipa_domain.lower()
realm = ipa_domain.upper()
realm_ldap = 'dc=' + ',dc='.join(domain_components)

install_with_dns = default('configurations/freeipa/install_with_dns', True)
install_with_dns = kc.trueorfalse(install_with_dns)
default_shell = default('configurations/freeipa/default_shell', '/bin/bash')

# Only except IPv4 for now
forwarders = default('configurations/freeipa/forwarders', '10.0.0.10').split(',')
forwarders = [forwarder.strip() for forwarder in forwarders]
forwarders = [forwarder for forwarder in forwarders if re.match('\\d+\\.\\d+\\.\\d+\\.\\d+', forwarder)]

forwarders_to_add ='\n'.join(['nameserver ' + f for f in forwarders])

client_init_wait = default('configurations/freeipa/client_init_wait', 600)

all_hosts = default("/clusterHostInfo/all_hosts", None)

ldap_bind_user = kc.default('configurations/freeipa/ldap_bind_user', 'kave_bind_user', kc.is_valid_username)
ldap_bind_services = ['twiki', 'gitlab', 'jenkins']

initial_users_and_groups = default('configurations/freeipa/initial_users_and_groups', '{"Users": [], "Groups" : {}}')
initial_users_and_groups = json.loads(initial_users_and_groups)

initial_user_passwords = default('configurations/freeipa/initial_user_passwords', '{ }')
initial_user_passwords = json.loads(initial_user_passwords)

initial_sudoers = default('configurations/freeipa/initial_sudoers',
                          '{ "Users": [], "Groups":[], "cmdcat": "all", "hostcat": "all", '
                          + '"runasusercat": "all", "runasgroupcat": "all" }')
initial_sudoers = json.loads(initial_sudoers)

kadm5acl_template = default('configurations/freeipa/kadm5acl_template', """*/admin@{{realm}} *
admin@{{realm}} *
admin@{{realm}} a *
admin@{{realm}} i *
admin@{{realm}} x *
admin@{{realm}} m *
""")

resolvconf_template = default('configurations/freeipa/resolvconf_template', """search {{domain}}
nameserver {{ipa_server_ip_address}}
nameserver 127.0.0.1
""")

for user, passwd in initial_user_passwords.iteritems():
    if len(passwd) < 8:
        raise ValueError("User : " + user + " cannot be assigned an intital password less than 8 characters")
    else:
        Logger.sensitive_strings[passwd] = "[PROTECTED]"

# JCE Installation
searchpath = default('configurations/freeipa/searchpath',
                     '/usr/lib/jvm/java-1.8*:/usr/lib/jvm/java-1.7*:/usr/jdk64/jdk1.7*:/usr/jdk64/jdk1.8*')
# folderpath="/jre/lib/security:/lib/security"
folderpath = default('configurations/freeipa/folderpath', '/jre/lib/security:/lib/security')

admin_user_shell = kc.default('configurations/freeipa/admin_user_shell', '/sbin/nologin', kc.is_valid_directory)

install_distribution_user = kc.default('configurations/freeipa/install_distribution_user', 'root')
