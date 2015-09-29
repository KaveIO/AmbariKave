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
installation_dir = default('configurations/jboss/installation_dir', '/opt/jboss-as/')
jboss_conf_file = installation_dir + "/standalone/configuration/standalone.xml"
mgmt_users_file = installation_dir + "/standalone/configuration/mgmt-users.properties"

management_user = 'admin'
management_password = default('configurations/jboss/management_password', "NOTAPASSWORD")
if management_password == "NOTAPASSWORD":
    management_password = False

# ip adresses the service will be listening on
ip_address = default('configurations/jboss/ip_address', '0.0.0.0')
ip_address_management = default('configurations/jboss/ip_address_management', '127.0.0.1')

# Port configurations
http_port = default('configurations/jboss/http_port', "8080")
https_port = default('configurations/jboss/https_port', '8443')
management_native_port = default('configurations/jboss/management_native_port', '9999')
management_http_port = default('configurations/jboss/management_http_port', '9990')
management_https_port = default('configurations/jboss/management_https_port', '9443')
ajp_port = default('configurations/jboss/ajp_port', '8009')
osgi_http_port = default('configurations/jboss/osgi_http_port', '8090')
remoting_port = default('configurations/jboss/remoting_port', '4447')
txn_recovery_environment_port = default('configurations/jboss/txn_recovery_environment_port', '4712')
txn_status_manager_port = default('configurations/jboss/txn_status_manager_port', '4713')

mail_server = default('configurations/jboss/mail_server', 'localhost')
mail_port = default('configurations/jboss/mail_port', '25')
