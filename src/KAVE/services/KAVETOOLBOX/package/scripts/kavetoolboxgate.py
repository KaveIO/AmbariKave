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
import sys
import os
import shutil

from resource_management import *
from kavetoolbox import KaveToolbox


class KaveToolboxGate(KaveToolbox):
    kind = "workstation"
    status_file = "/etc/kave/status"

    def status(self, env):
        with open(self.status_file, 'r') as content_file:
            content = content_file.read()
        if int(content) != 0:
            raise ComponentIsNotRunning()
        return True

    def start(self, env):
        Execute("echo 0 > " + self.status_file)

    def stop(self, env):
        Execute("echo 1 > " + self.status_file)

    def restart(self, env):
        Execute("echo 0 > " + self.status_file)

if __name__ == "__main__":
    KaveToolboxGate().execute()
