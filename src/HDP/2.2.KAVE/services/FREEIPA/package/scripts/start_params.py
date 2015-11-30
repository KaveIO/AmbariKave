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

from resource_management import *

config = Script.get_config()

hostname = config["hostname"]
ipa_server = default("/clusterHostInfo/ambari_server_host", [False])[0]

hostname_components = config["hostname"].split('.')
if len(hostname_components) < 3:
    raise Exception('FreeIPA hostname is not a FQDN. installation not possible')

realm = '.'.join(hostname_components[1:]).upper()
domain = '.'.join(hostname_components[1:])

ipa_server = default("/clusterHostInfo/ambari_server_host", [False])[0]

kadm5acl_template = default('configurations/freeipa/kadm5acl_template',"""*/admin@{{realm}} *
admin@{{realm}} *
admin@{{realm}} a *
admin@{{realm}} i *
admin@{{realm}} x *
admin@{{realm}} m *
""")

resolvconf_template = default('configurations/freeipa/resolvconf_template',"""search {{domain}}
nameserver {{ipa_server_ip_address}}
""")

ipa_server_ip_address = socket.gethostbyname(ipa_server)
if not ipa_server_ip_address:
    raise Exception('ipa_server_ip_address couldn\'t be determined')