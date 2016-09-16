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
import kavecommon as kc


config = Script.get_config()

hostname = config["hostname"]

www_folder = kc.default('configurations/apache/www_folder', '/var/www/html/', kc.is_valid_directory)

PORT = kc.default('configurations/apache/PORT', '80', kc.is_valid_port)
servername = default('configurations/apache/servername', hostname)
if servername == "hostname":
    servername = hostname

template_000_default = default('configurations/apache/template_000_default', """# Created automatically with Ambari
# All manual changes will be undone in the case of a server restart
# Edit the template through the Ambari interface instead
TraceEnable Off
RequestHeader unset Proxy early
ServerSignature Off
ServerTokens Prod
Options -Multiviews
Listen {{PORT}}
ServerName "{{servername}}"
DocumentRoot "{{www_folder}}"
""")
