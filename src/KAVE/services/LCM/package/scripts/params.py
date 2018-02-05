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

lcm_releaseversion = default('/configurations/lcm_application/lcm_releaseversion', '0.2.4-SNAPSHOT')

lcm_application_name = config["configurations"]["lcm_application"]["lcm_application_name"]

lcm_service_user = config["configurations"]["lcm_application"]["lcm_service_user"]

lcm_install_dir  = config["configurations"]["lcm_application"]["lcm_install_dir"]

lcm_home_dir = lcm_install_dir + '/lcm-complete-' + lcm_releaseversion + '/'

LCM_UI_URL = kc.default('configurations/lcm_application/LCM_UI_URL', hostname, kc.is_valid_hostname)

LCM_UI_PORT = kc.default('configurations/lcm_application/LCM_UI_PORT', '8081', kc.is_valid_port)

LCM_SecureUI_Port = kc.default('configurations/lcm_application/Lcm_SecureUI_Port', '4444', kc.is_valid_port)

LCM_Server_URL = kc.default('configurations/lcm_application/LCM_Server_URL', hostname, kc.is_valid_hostname)

LCM_Server_PORT = kc.default('configurations/lcm_application/LCM_Server_PORT', '8085', kc.is_valid_port)

LCM_SecureServer_Port = kc.default('configurations/lcm_application/LCM_SecureServer_Port', '4445', kc.is_valid_port)

LCM_Swagger_PORT = kc.default('configurations/lcm_application/LCM_Swagger_PORT', '8083', kc.is_valid_port)

sever_log_file_path = default('configurations/lcm_logs/sever_log_file_path', 'logs/lcm-server.log')

server_log_file_size = default('confgigurations/lcm_logs/server_log_file_size', '20M')

ui_log_file_path = default('configurations/lcm_logs/ui_log_file_path', 'logs/lcm-ui.log')

ui_log_file_size = default('configurations/lcm_logs/ui_log_file_size', '20MB')

Security_truststoreType = default('configurations/lcm_security/Security.truststoreType', 'JKS')

lcm_server_security_encryption_key = default('configurations/lcm_security/lcm_server_security_encryption_key', '123456789qwertyu')

lcm_admin_password = default('configurations/lcm_security/lcm_admin_password', 'admin')

lcm_mongodb_host = default('/clusterHostInfo/mongodb_master_hosts', [None])[0]
if lcm_mongodb_host == hostname:
    lcm_mongodb_host = 'localhost'
if not lcm_mongodb_host:
    raise ValueError("Could not locate MongoDB server, did you install it in the cluster?")

lcm_mongodb_port = kc.default('configurations/mongodb/tcp_port', '27017', kc.is_valid_port)

application_properties = config["configurations"]["lcm_application"]["application_properties"]

security_properties = config["configurations"]["lcm_security"]["security.properties"]

log4j_server_properties = config["configurations"]["lcm_logs"]["log4j-server_properties"]

log4j_ui_properties = config["configurations"]["lcm_logs"]["log4j-ui_properties"]