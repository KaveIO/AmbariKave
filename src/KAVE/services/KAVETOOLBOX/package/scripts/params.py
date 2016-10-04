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

top_dir = kc.default("configurations/kavetoolbox/top_dir", "/opt/", kc.is_valid_directory)
releaseversion = default('configurations/kavetoolbox/releaseversion', "3.0-Beta")
alternative_download = default('configurations/kavetoolbox/alternative_download', "none")
ignore_missing_groups = default('configurations/kavetoolbox/ignore_missing_groups', "False")
ignore_missing_groups = kc.trueorfalse(ignore_missing_groups)
command_line_args = default('configurations/kavetoolbox/command_line_args', "False")
try:
    command_line_args = kc.trueorfalse(command_line_args)
except TypeError, ValueError:
    if type(command_line_args) is str:
        pass
    else:
        print "could not interpret value of command_line_args correctly"
        raise
custom_install_template_default = """
# -------------------------------
import kavedefaults as cnf

cnf.li.InstallTopDir="{{top_dir}}"

# -------------------------------
"""
custom_install_template = default('configurations/kavetoolbox/custom_install_template', custom_install_template_default)
if alternative_download == "none":
    alternative_download = ""
