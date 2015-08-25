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
from resource_management import *

config = Script.get_config()

hostname = config["hostname"]

www_folder = default('configurations/twiki/www_folder', '/var/www/html/')
install_dir = www_folder + "twiki/"
PORT = default('configurations/twiki/PORT', '80')
servername = default('configurations/twiki/servername', hostname)
if servername == "default":
    servername = hostname
admin_user = default('configurations/twiki/admin_user', 'twiki-admin')

ldap_group = 'twiki'

# ldap configuration
ldap_enabled = default('configurations/twiki/ldap_enabled', 'False')
ldap_enabled = (ldap_enabled.lower()=='true' or ldap_enabled.lower().startswith('y'))
freeipa_host = default('/clusterHostInfo/freeipa_server_hosts', [False])[0]
if freeipa_host and ldap_enabled:
    freeipa_host_components = freeipa_host.lower().split('.')
    if len(freeipa_host_components) >= 3:
        ldap_host = freeipa_host
        ldap_port = '636'
        ldap_uid = 'uid'
        ldap_bind_user = default('configurations/twiki/ldap_bind_user', 'kave_bind_user')
        #ldap_group = default('configurations/twiki/ldap_group', 'twiki')
        ldap_bind_password = default('configurations/twiki/ldap_bind_password', False)
        if not ldap_bind_password:
            raise Exception('If you want to use ldap, you must have an ldap_bind_user with a known password')
        ldap_base = 'dc='+',dc='.join(freeipa_host_components[1:])
    else:
        raise Exception('freeipa_host was provided for twiki installation but no FQDN could be determined from this.')
else:
    print 'ldap not integrated '
