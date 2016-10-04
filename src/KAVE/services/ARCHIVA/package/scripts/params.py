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

install_topdir = kc.default('configurations/archiva/install_topdir', '/opt/', kc.is_valid_directory)

if len(install_topdir) < 4 or install_topdir.count('/') < 2 or not install_topdir.startswith('/'):
    raise ValueError('archiva/install_topdir must be a valid directory full path,'
                     ' with a length of at least 4 and two /')

if not install_topdir.endswith('/'):
    install_topdir = install_topdir + '/'

install_subdir = default('configurations/archiva/install_subdir', 'archiva')

if not len(install_subdir) or install_subdir.count('/'):
    raise ValueError('archiva/install_subdir must be a simple string, with no "/"')

archiva_jetty_port = kc.default('configurations/archiva/archiva_jetty_port', '5050', kc.is_valid_port)

ARCHIVA_ADMIN = kc.default("configurations/archiva/ARCHIVA_ADMIN", "admin", kc.is_valid_username)
ARCHIVA_ADMIN_FULLNAME = default("configurations/archiva/ARCHIVA_ADMIN_FULLNAME", "administrator")
ARCHIVA_ADMIN_EMAIL = default("configurations/archiva/ARCHIVA_ADMIN_EMAIL", "default")
ARCHIVA_ADMIN_PASSWORD = config['configurations']["archiva"]["ARCHIVA_ADMIN_PASSWORD"]
Logger.sensitive_strings[ARCHIVA_ADMIN_PASSWORD] = "[PROTECTED]"

if ARCHIVA_ADMIN_EMAIL == 'default':
    ARCHIVA_ADMIN_EMAIL = ARCHIVA_ADMIN + '@' + '.'.join(hostname.split('.')[1:])

kc.is_valid_emailid(ARCHIVA_ADMIN_EMAIL, "archiva/ARCHIVA_ADMIN_EMAIL")

archiva_admin_dict = {"username": ARCHIVA_ADMIN, "password": ARCHIVA_ADMIN_PASSWORD,
                      "confirmPassword": ARCHIVA_ADMIN_PASSWORD, "fullName": ARCHIVA_ADMIN_FULLNAME,
                      "email": ARCHIVA_ADMIN_EMAIL, "assignedRoles": [], "modified": 'true', "rememberme": 'false',
                      "logged": 'false'}
