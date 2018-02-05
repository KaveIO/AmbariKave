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
from resource_management.core.system import System
import os
import string
import kavecommon as kc

config = Script.get_config()

hostname = config["hostname"]

systemd_lcmserver_unitfile_path = "/usr/lib/systemd/system/lcm-server.service"

systemd_lcmui_unitfile_path = "/usr/lib/systemd/system/lcm-ui.service"

lcm_releaseversion = default('/configurations/lcm/lcm_releaseversion', '0.2.4-SNAPSHOT')

lcm_service_user = kc.default('configurations/lcm/lcm_service_user', 'lcm', kc.is_valid_username)

lcm_install_dir  = kc.default('configurations/lcm/lcm_install_dir ', '/opt/lcm', kc.is_valid_directory)

lcm_home_dir = lcm_install_dir + '/lcm-complete-' + lcm_releaseversion + '/'

LCM_UI_URL = kc.default('configurations/lcm/LCM_UI_URL', hostname, kc.is_valid_hostname)

LCM_UI_PORT = kc.default('configurations/lcm/Lcm_UI_PORT', '8081', kc.is_valid_port)

LCM_SecureUI_Port = kc.default('configurations/lcm/Lcm_SecureUI_Port', '4444', kc.is_valid_port)

LCM_Server_URL = kc.default('configurations/lcm/LCM_Server_URL', hostname, kc.is_valid_hostname)

LCM_Server_PORT = kc.default('configurations/lcm/LCM_Server_PORT', '8085', kc.is_valid_port)

LCM_SecureServer_Port = kc.default('configurations/lcm/LCM_SecureServer_Port', '4445', kc.is_valid_port)

LCM_Swagger_PORT = kc.default('configurations/lcm/LCM_Swagger_PORT', '8083', kc.is_valid_port)

application_properties = config["configurations"]["lcm"]["application_properties"] 

sever_log_file_path = default('configurations/lcm/sever_log_file_path', 'logs/lcm-server.log')

server_log_file_size = default('confgigurations/lcm/server_log_file_size', '20M')

ui_log_file_path = default('configurations/lcm/ui_log_file_path', 'logs/lcm-ui.log')

ui_log_file_size = default('configurations/lcm/ui_log_file_size', '20MB')

log4j_server_properties = default('configurations/lcm/log4j-server_properties', """""")

log4j_ui_properties = default('configurations/lcm/log4j-ui_properties',  """""")

Security_truststoreType = default('configurations/lcm/Security.truststoreType', 'JKS')

lcm_server_security_encryption_key = default('configurations/lcm/lcm_server_security_encryption_key', '123456789qwertyu')

security_properties = default('configurations/lcm/security.properties', """""")

lcm_admin_password = default('configurations/lcm/lcm_admin_password', 'admin')

lcm_mongodb_host = default('/clusterHostInfo/mongodb_master_hosts', [None])[0]
if lcm_mongodb_host == hostname:
    lcm_mongodb_host = 'localhost'
if not lcm_mongodb_host:
    raise ValueError("Could not locate MongoDB server, did you install it in the cluster?")

lcm_mongodb_port = kc.default('configurations/mongodb/tcp_port', '27017', kc.is_valid_port)

