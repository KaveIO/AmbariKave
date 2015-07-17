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

gitlab_conf_file = "/etc/gitlab/gitlab.rb"
gitlab_port = default("configurations/gitlab/gitlab_port", "80")
gitlab_url = default("configurations/gitlab/gitlab_url", hostname)
if not gitlab_url:
    raise Exception('gitlab_url set to an unusable value \'%s\'' % gitlab_url)

gitlab_signin_enabled = default('configurations/gitlab/gitlab_signin_enabled', 'true')
restrict_public_projects = default('configurations/gitlab/restrict_public_projects', 'true')

#postgre configuration in case it is already installed!
postgre_disabled = False
# doesn't work at the moment, check in gitlabs explicitly and throw an exception instead

# ldap configuration
ldap_enabled = False
freeipa_host = default('configurations/gitlab/freeipa_host', False)
if freeipa_host.lower()=="None":
    freeipa_host=False
if freeipa_host:
    freeipa_host_components = freeipa_host.lower().split('.')
    if len(freeipa_host_components) >= 3:
        ldap_enabled = True
        ldap_host = freeipa_host
        ldap_port = '636'
        ldap_uid = 'uid'
        ldap_method = 'ssl'
        ldap_allow_username_or_email_login = 'true'
        ldap_base = ',dc='.join(['cn=accounts'] + freeipa_host_components[1:])
    else:
        raise Exception('freeipa_host was provided for gitlabs installation but no FQDN could be determined from this.')
