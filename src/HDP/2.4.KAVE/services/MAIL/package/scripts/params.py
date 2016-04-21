##############################################################################
#
# Copyright 2016 KPMG N.V. (unless otherwise stated)
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

hostname = default('configurations/mail/hostname', config['hostname'])
if hostname == 'hostname':
    hostname = config['hostname']
domain = default('configurations/mail/domain', '.'.join(hostname.split('.')[1:]))
if domain == 'hostdomain':
    domain = '.'.join(hostname.split('.')[1:])

inet_interfaces = default('configurations/mail/inet_interfaces', 'all')
inet_protocols = default('configurations/mail/inet_protocols', 'ipv4')
message_size = default('configurations/mail/message_size', '10485760')
mailbox_size = default('configurations/mail/mailbox_size', '1073741824')
auth_mechanisms = default('configurations/mail/auth_mechanisms', 'login')
disable_planetext_auth = default('configurations/mail/disable_planetext_auth', 'no')
