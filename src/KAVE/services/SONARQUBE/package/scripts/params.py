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
import status_params

from resource_management import *
from ambari_commons.os_check import OSCheck
import kavecommon as kc

config = Script.get_config()
tmp_dir = Script.get_tmp_dir()

hostname = config["hostname"]

sonarqube_supported_plugins = ['sonar-python-plugin-1.5.jar']

sonarqube_install_directory = kc.default('configurations/sonarqube/sonarqube_install_directory',
                                         '/opt/sonarqube', kc.is_valid_directory)
sonarqube_runner_install_directory = kc.default('configurations/sonarqube/sonarqube_runner_install_directory',
                                                '/opt/sonarqube_runner',
                                                kc.is_valid_directory
                                                )
sonarqube_plugins = set()
for plugin in default('configurations/sonarqube/sonarqube_plugins', 'sonar-python-plugin-1.5.jar').split(','):
    if plugin == '':
        continue
    elif plugin in sonarqube_supported_plugins:
        sonarqube_plugins.add(plugin)
    else:
        print 'Ignoring unsupported plugin: %s' % plugin


known_authentication_methods = ['HBAC', 'NONE']
authentication_method = default('configurations/sonarqube/authentication_method', 'HBAC')
authentication_method = authentication_method.upper()
if authentication_method not in known_authentication_methods:
    raise ValueError("Authentication method not recognised, I only know "
                     + str(known_authentication_methods)
                     + " but you asked for " + authentication_method)
# enable_pam_auth configuration
enable_pam_auth = (authentication_method == "HBAC")


sonar_host = default('/clusterHostInfo/sonarqube_server_hosts', [None])[0]
if sonar_host == hostname:
    sonar_host = "localhost"
if not sonar_host:
    raise ValueError("Could not locate sonar server, did you install it in the cluster?")

sonar_web_port = kc.default('configurations/sonarqube/sonar_web_port', '5051', kc.is_valid_port)

sonar_database_url = default('/clusterHostInfo/sonarqube_mysql_server_hosts', [None])[0]
if sonar_database_url == hostname:
    sonar_database_url = 'localhost'
if not sonar_database_url:
    raise ValueError("Could not locate sonarqube sql server, did you install it in the cluster?")

sonar_database_user_name = kc.default(
    'configurations/sonarqube/sonar_database_user_name', 'sonarqube', kc.is_valid_username)
sonar_database_user_passwd = config['configurations']['sonarqube']['sonar_database_user_passwd']

if not sonar_database_user_passwd:
    raise Exception('sonar_database_user_passwd needs to be set')
else:
    Logger.sensitive_strings[sonar_database_user_passwd] = "[PROTECTED]"

mysql_adduser_path = format("{tmp_dir}/addMysqlUser.sh")
mysql_deluser_path = format("{tmp_dir}/removeMysqlUser.sh")

daemon_name = status_params.daemon_name

jvmpath = default('configurations/sonarqube/jvmpath',
                  '/usr/lib/jvm/java-1.8*:/usr/lib/jvm/jre-1.7.0-openjdk*:'
                  '/usr/lib/jvm/java-1.7*:/usr/jdk64/jdk1.7*:/usr/jdk64/jdk1.8*')

if OSCheck.is_ubuntu_family():
    mysql_configname = '/etc/mysql/my.cnf'
else:
    mysql_configname = '/etc/my.cnf'
