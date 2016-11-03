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
import base
import os
from resource_management import *
from subprocess import Popen, PIPE


def node_tunnelling(gateport, node, nodeport, pub_key_path,user):

    process = Popen(['ssh', '-i', pub_key_path, '-L', gateport, ':', node, ':', nodeport, user ,'@', node], stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()

    if stderr:
        print "Please check the bash command"

    return


if __name__ == "__main__":
    import sys

    branch = "__local__"
    if "--verbose" in sys.argv:
        verbose = True
        sys.argv = [s for s in sys.argv if s != "--verbose"]
    if "--branch" in sys.argv:
        branch = "__service__"
        sys.argv = [s for s in sys.argv if s != "--branch"]
    if "--this-branch" in sys.argv:
        branch = "__local__"
        sys.argv = [s for s in sys.argv if s != "--this-branch"]
    #if "--gateport" in sys.argv:
    #    sys.argv = [s for s in sys.argv if s != "--gateport"]
    #if "--node" in sys.argv:
    #    sys.argv = [s for s in sys.argv if s != "--node"]
    #if "--nodeport" in sys.argv:
    #    sys.argv = [s for s in sys.argv if s != "--nodeport"]
    if len(sys.argv) < 2:
        raise KeyError("You must specify which service to test")

    gateport = sys.argv[1]
    node = sys.argv[2]
    nodeport = sys.argv[3]
    pub_key_path = sys.argv[4]
    user = sys.argv[5]

    if len(sys.argv) >= 5:
        node_tunnelling(gateport, node, nodeport, pub_key_path, user)
    else:
        raise KeyError("You must specify all the parameters")


