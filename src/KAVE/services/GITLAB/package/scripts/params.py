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
from resource_management import *
import kavecommon as kc

config = Script.get_config()

hostname = config["hostname"]

gitlab_conf_file = "/etc/gitlab/gitlab.rb"
gitlab_port = kc.default("configurations/gitlab/gitlab_port", "80", kc.is_valid_port)
gitlab_url = kc.default("configurations/gitlab/gitlab_url", hostname, kc.is_valid_hostname)
unicorn_port = kc.default("configurations/gitlab/unicorn_port", "8080", kc.is_valid_port)
unicorn_interface = default("configurations/gitlab/unicorn_interface", '127.0.0.1')

if gitlab_url == 'hostname':
    gitlab_url = hostname
if not gitlab_url:
    raise Exception('gitlab_url set to an unusable value \'%s\'' % gitlab_url)

gitlab_signin_enabled = default('configurations/gitlab/gitlab_signin_enabled', 'true')
gitlab_signin_enabled = kc.trueorfalse(gitlab_signin_enabled)
gitlab_admin_password = config['configurations']['gitlab']['gitlab_admin_password']
Logger.sensitive_strings[gitlab_admin_password] = "[PROTECTED]"
restrict_public_projects = default('configurations/gitlab/restrict_public_projects', 'true')
restrict_public_projects = kc.trueorfalse(restrict_public_projects)

# postgre configuration in case it is already installed!
postgre_disabled = False
# doesn't work at the moment, check in gitlabs explicitly and throw an exception instead
ldap_group = ''
ldap_admin_group = ''

# ldap configuration
ldap_enabled = False
freeipa_host = default('/clusterHostInfo/freeipa_server_hosts', [False])[0]
if freeipa_host:
    freeipa_host_components = freeipa_host.lower().split('.')
    if len(freeipa_host_components) >= 3:
        ldap_enabled = True
        ldap_host = freeipa_host
        ldap_port = '636'
        ldap_uid = 'uid'
        ldap_method = 'ssl'
        ldap_allow_username_or_email_login = 'true'
        # ldap_group = default('configurations/gitlab/ldap_group', 'gitlab')
        # ldap_admin_group = default('configurations/gitlab/ldap_admin_group', 'admins')
        ldap_base = ',dc='.join(['cn=accounts'] + freeipa_host_components[1:])
    else:
        raise Exception('freeipa_host was provided for gitlabs installation but no FQDN could be determined from this.')

gitlabrb = default('configurations/gitlab/gitlabrb', """# Created automatically with Ambari
# All manual changes will be undone in the case of a server restart
# Edit the template through the Ambari interface instead

# Change the external_url to the address your users will type in their browser
external_url 'http://{{gitlab_url}}:{{gitlab_port}}'

{% if ldap_enabled %}
gitlab_rails['ldap_enabled'] = true
gitlab_rails['ldap_host'] = '{{ldap_host}}'
gitlab_rails['ldap_port'] = {{ldap_port}}
gitlab_rails['ldap_uid'] = '{{ldap_uid}}'
gitlab_rails['ldap_method'] = '{{ldap_method}}'
gitlab_rails['ldap_allow_username_or_email_login'] = {{ldap_allow_username_or_email_login}}
gitlab_rails['ldap_base'] = '{{ldap_base}}'
#gitlab_rails['ldap_user_filter'] = '(memberOf=CN={{ldap_group}},{{ldap_base}})'
#gitlab_rails['admin_group'] = '{{ldap_admin_group}}'
{% endif %}

gitlab_rails['initial_root_password'] = '{{gitlab_admin_password}}'

{% if not gitlab_signin_enabled %}
gitlab_rails['gitlab_signin_enabled'] = false
{% endif %}

{% if restrict_public_projects %}
gitlab_rails['gitlab_restricted_visibility_levels'] = [ "public" ]
{% endif %}

{% if postgre_disabled %}
# Disable the built-in Postgres? This doesn't work for the moment, leave here as a placeholder for the full solution
postgresql['enable'] = false

gitlab_rails['db_adapter'] = 'postgresql'
gitlab_rails['db_encoding'] = 'unicode'
# Create database manually and place its name here.
gitlab_rails['db_database'] = 'gitlabhq_production'
gitlab_rails['db_host'] = '127.0.0.1'
gitlab_rails['db_port'] = '5432'
gitlab_rails['db_username'] = 'git' # Database owner.
gitlab_rails['db_password'] = '{{gitlab_admin_password}}' # Database owner's password.
{% endif %}

unicorn['port']={{unicorn_port}}
unicorn['listen']='{{unicorn_interface}}'
""")
