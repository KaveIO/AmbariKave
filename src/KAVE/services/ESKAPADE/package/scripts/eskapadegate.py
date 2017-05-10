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
# from Eskapade import Eskapade


class EskapadeGate():
    kind = "workstation"

    def start(self, env):
        return True

    def stop(self, env):
        return True

    def status(self, env):
        return True


if __name__ == "__main__":
    EskapadeGate().execute()
