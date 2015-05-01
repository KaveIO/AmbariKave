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
    
ldap_integration_enabled = default('configurations/twiki/ldap_integration_enabled', False)
if ldap_integration_enabled:
    ldap_server = default("configurations/twiki/ldap_server", False)
    ldap_bind_user = default('configurations/twiki/ldap_bind_user', False)
    ldap_bind_password = default('configurations/twiki/ldap_bind_password', False)
    ldap_base = default('configurations/twiki/ldap_base', False)
    ldap_port = default('configurations/twiki/ldap_port', 389)
    
    if not ldap_server:
        ldap_server = default("/clusterHostInfo/ambari_server_host", [False])[0]
        if not ldap_server:
            raise Exception('LDAP integration is enabled however ldap_server was False')
    if not ldap_bind_user:
        raise Exception('LDAP integration is enabled however ldap_bind_user was False')
    if not ldap_bind_password:
        raise Exception('LDAP integration is enabled however ldap_bind_password was False')
    
    if not ldap_base:
        ldap_server_components = ldap_server.split('.')
        if len(ldap_server_components) < 3:
            raise Exception('LDAP hostname is not a FQDN. installation not possible')
        ldap_base = 'dc='+',dc='.join(ldap_server_components[1:])
else:    
    print 'ldap not integrated '
