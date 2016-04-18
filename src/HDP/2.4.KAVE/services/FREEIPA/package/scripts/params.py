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
import re
import socket
import json
import kavecommon as kc

from resource_management import *

config = Script.get_config()

hostname = config["hostname"]

amb_server = default("/clusterHostInfo/ambari_server_host", [False])[0]

ipa_server = default("/clusterHostInfo/freeipa_server_hosts", [False])[0]

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

hostname_components = config["hostname"].split('.')
if len(hostname_components) < 3:
    raise Exception('FreeIPA hostname is not a FQDN. installation not possible')
domain = '.'.join(hostname_components[1:])
realm = '.'.join(hostname_components[1:]).upper()
realm_ldap = 'dc=' + ',dc='.join(hostname_components[1:])

install_with_dns = default('configurations/freeipa/install_with_dns', True)
install_with_dns = kc.trueorfalse(install_with_dns)
default_shell = default('configurations/freeipa/default_shell', '/bin/bash')

# Only except IPv4 for now
forwarders = default('configurations/freeipa/forwarders', '8.8.8.8').split(',')
forwarders = [forwarder.strip() for forwarder in forwarders]
forwarders = [forwarder for forwarder in forwarders if re.match('\\d+\\.\\d+\\.\\d+\\.\\d+', forwarder)]

client_init_wait = default('configurations/freeipa/client_init_wait', 600)

all_hosts = default("/clusterHostInfo/all_hosts", [hostname])

ldap_bind_user = default('configurations/freeipa/ldap_bind_user', 'kave_bind_user')
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
