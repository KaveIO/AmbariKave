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
"""
Open ssh tunnel to remote machine. Creates the passed user if not existing on the remote machine
and generate new ssh keys for it.
:param 1: gate port to forward
:param 2: node IP to connect to
:param 3: node port to forward
:param 4: public key path for ssh auth
:param 5: user to be used for the connection or create new one if missing
"""

from resource_management import *
from subprocess import Popen, PIPE


def node_tunneling(gateport, node, nodeport, pub_key_path, user):

    process = Popen(['ssh', '-i', pub_key_path, '-L', gateport, ':', node, ':',
                     nodeport, user, '@', node], stdout=PIPE, stderr=PIPE)
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
    if "--gateport" in sys.argv:
        sys.argv = [s for s in sys.argv if s != "--gateport"]
    if "--node" in sys.argv:
        sys.argv = [s for s in sys.argv if s != "--node"]
    if "--nodeport" in sys.argv:
        sys.argv = [s for s in sys.argv if s != "--nodeport"]
    if len(sys.argv) < 2:
        raise KeyError("Insufficient arguments")

    gateport = sys.argv[1]
    node = sys.argv[2]
    nodeport = sys.argv[3]
    pub_key_path = sys.argv[4]
    user = sys.argv[5]

    cmd = "chmod u+x user_check.sh"
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    p.wait()

    if user not in ['centos', 'root']:
        new_user = input('Enter the username:')

        cmd = "user_check.sh" + new_user
        p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()

        if not stdout:
            process = Popen(['useradd', new_user])
            stdout, stderr = process.communicate()

            Execute('ssh-keygen -t rsa')
            process = Popen(['ssh-copy-id', node])

        else:
            raise KeyError("User exist")

        new_user_pub_key_path = '/home/' + new_user + '/.ssh/id_rsa.pub'

    if len(sys.argv) >= 5:
        if pub_key_path and user in ['centos', 'root']:
            node_tunneling(gateport, node, nodeport, pub_key_path, user)
        else:
            node_tunneling(gateport, node, nodeport, new_user_pub_key_path, new_user)
    else:
        raise KeyError("You must specify all the parameters")
