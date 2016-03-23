#!/usr/bin/env python
##############################################################################
#
# Copyright 2015 KPMG N.V. (unless otherwise stated)
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
This is the createkeytabs script of the KAVE FreeIPA implementation

usage:
    kinit admin
    createkeytabs.py kerberos.csv

instructions:
   MUST be run from the ambari node, where FreeIPA is also installed, as the root user
   kinit [someadminuser] must be called beforehand
   - because only the ambari node root user can ssh over the whole cluster
   - because it's best to create all the users/keytabs on the admin node
   - because kinit is necessary to authenticate with FreeIPA

explanation:
   The Ambari kerberization process gives you the chance to download a csv
   containing a list of needed keytabs. This keytabs file lists all the bits
   and pieces HDFS/yarn components need to operate a fully kerberized cluster.
   Late creation of these keytabs is better, the list is likely to change.
   Save this file locally and run this script over that file

operation:
   For each line in the kerberos.csv file
   a) Check that the machine named exists within the cluster
   b) Check/fix that the user named exists with the named group

   Then loop again in order to:
   c) Create any principles / keytabs and control permissions
   d) Copy keytabs to all machines and control permissions

   Then finally
   e) Check: su <user> /usr/bin/kinit -kt <keytab> <identity>
"""
import sys
import os
import subprocess as sub

try:
    import freeipa
except ImportError:
    if os.path.exists("{{scriptpath}}/freeipa.py"):
        sys.path.append("{{scriptpath}}")
    else:
        relp = os.path.realpath(os.path.dirname(__file__) + "/../scripts/")
        if os.path.exists(relp + "/freeipa.py"):
            sys.path.append(relp)
    import freeipa


def popen(cmd, exit=True, shell=None):
    """ Wrapper around popen """
    if shell is None:
        if type(cmd) is str and (' ' in cmd):
            shell = True
        else:
            shell = False
    proc = sub.Popen(cmd, shell=shell, stdout=sub.PIPE, stderr=sub.PIPE)
    output, err = proc.communicate()
    status = proc.returncode
    if status and exit:
        raise RuntimeError("Problem running: \n" + str(cmd) + "\n got:\n\t"
                           + str(status) + "\n from stdout: \n" + output + " stderr: \n" + err)
    elif status:
        print >> sys.__stderr__, ("ERROR: " + "Problem running: \n" + str(cmd) + "\n got:\n\t"
                                  + str(status) + "\n from stdout: \n" + output + " stderr: \n" + err)

    return output.strip()


class Remote(object):
    """
    Wrapper around ssh and scp for this script
    If localhost, don't use ssh
    """

    def __init__(self, host, user='root'):
        self.user = user
        self.host = host

    def check(self, firsttime=True):
        """
        verify if I can access this host. If firsttime=True i will temporarily ignore the known_hosts file
        """
        if self.host == 'localhost':
            return True

        extrasshopts = []
        if firsttime:
            sshopts = ["-o", "UserKnownHostsFile=/dev/null", "-o", "StrictHostKeyChecking=no", "-o",
                       "PasswordAuthentication=no", "-o", "ConnectTimeout=3"]
        out = self.run("echo Hello World from $HOSTNAME", sshopts=sshopts, exit=False)
        if "Hello World" not in out or "HOSTNAME" in out:
            raise ValueError(
                "Unable to contact machine " + self.user + "@" + self.host + "! or machine did not respond correctly")
        return True

    def run(self, cmd, sshopts=[], exit=True):
        """
        run a command through ssh
        """
        if self.host == 'localhost':
            return popen(cmd)

        if type(cmd) is str:
            cmd = cmd.strip()
            cmd = [cmd]
        cmd = [' '.join(cmd)]
        return popen(["ssh"] + sshopts + [self.user + "@" + self.host] + cmd)

    def cp(self, local, remote, sshopts=[]):
        """
        Copy file or directory to the remote machine through scp
        """
        if self.host == 'localhost':
            return popen(['cp', local, remote])

        if not os.path.exists(os.path.realpath(os.path.expanduser(local))):
            raise IOError("file to copy must exist " + local)
        directory = os.path.isdir(os.path.realpath(os.path.expanduser(local)))
        if directory and "-r" not in sshopts:
            sshopts.append("-r")
        return popen(["scp"] + sshopts + [local, self.user + "@" + self.host + ":" + remote])


def yieldConfig(filename):
    """
    CSV iterator
    """
    with open(filename) as fp:
        topline = fp.readline().strip().split(',')
        for line in fp:
            if len(line.strip()):
                yield dict((n, v) for n, v in zip(topline, line.strip().split(',')))

if __name__ == "__main__":
    if "--help" in sys.argv:
        print __doc__
        sys.exit(0)
    if len(sys.argv) < 2:
        raise AttributeError("Supply the name of the kerberos keytabs csv file")
    # Todo, check if the user has done kinit!
    # simple test that this works
    ipa = freeipa.FreeIPACommon()
    if not ipa.group_exists('admins'):
        raise SystemError("No ipa group admins found ... did you forget to kinit or are you"
                          "Running in some strange configuration??")
    # grab csv from iterator. The whole thing since I need to do multiple iterations
    keytabs = [k for k in yieldConfig(sys.argv[-1])]
    # test that all machines are contactable
    for keytab in keytabs:
        remote = Remote(keytab["host"])
        remote.check()
    # add local users if required, fix groups if required
    for keytab in keytabs:
        remotes = [Remote(keytab["host"]), Remote("localhost")]
        # add groups if they do not exist
        for remote in remotes:
            if keytab["keytab file group"] not in remote.run("cut -d: -f1 /etc/group"):
                remote.run("groupadd " + keytab["keytab file group"])
        if keytab["principal type"] == "USER":
            continue
        if keytab["keytab file owner"] is "root":
            continue
        # add users if they do not exist
        for remote in remotes:
            for user in [keytab["local username"], keytab["keytab file owner"]]:
                if user == 'root':
                    continue
                if not len(user):
                    continue
                try:
                    remote.run("grep " + user + " /etc/passwd > /dev/null")
                except RuntimeError:
                    remote.run("useradd " + user)
                if keytab["keytab file group"] not in remote.run("groups " + user):
                    remote.run("usermod -a -G " + keytab["keytab file group"] + " " + user)
    #  c) Create any principles / keytabs and control permissions
    #  d) Copy keytabs to required machines and control permissions
    already_created = []
    for keytab in keytabs:
        identity = keytab["principal name"].split('@')[0]
        realm = keytab["principal name"].split('@')[-1]
        if not len(identity):
            raise NameError("I could not interpret the identity of " + str(keytab))
        if not len(realm):
            raise NameError("I could not interpret the realm of " + str(keytab))
        if keytab["principal type"] == "USER":
            ipa.create_user_principal(identity)
        if keytab["principal type"] == "SERVICE":
            ipa.create_service_principal(identity)
        intermediate_file = keytab["keytab file path"] + identity.replace('/', '_')
        if not len(keytab["keytab file path"]):
            continue
        if intermediate_file not in already_created:
            if os.path.exists(intermediate_file):
                popen('rm -f ' + intermediate_file)
            if (identity in ["HTTP/" + popen("hostname -f")]
                    and os.path.exists('/etc/httpd/conf/ipa.keytab')):
                # Special case for HTTP, needed by the FreeIPA server!
                popen("cp /etc/httpd/conf/ipa.keytab " + intermediate_file)
                popen("chown " + keytab["keytab file owner"] + ":" + keytab["keytab file group"]
                      + " " + keytab["keytab file path"])
                popen("chmod " + keytab["keytab file mode"] + " " + intermediate_file)
            else:
                ipa.create_keytab(popen("hostname -f"), identity, realm,
                                  file=intermediate_file,
                                  user=keytab["keytab file owner"],
                                  group=keytab["keytab file group"],
                                  permissions=keytab["keytab file mode"]
                                  )
            already_created.append(intermediate_file)
        remote = Remote(keytab["host"])
        exists = remote.run("bash -c 'if [-d " + os.path.dirname(keytab["keytab file path"])
                            + " ]; then echo \"yes\"; fi; '")
        exists = 'yes' in exists
        if not exists:
            remote.run("mkdir -p " + os.path.dirname(keytab["keytab file path"]))

        remote.cp(intermediate_file, keytab["keytab file path"])
        remote.run("chown "
                   + keytab["keytab file owner"] + ":" + keytab["keytab file group"]
                   + " " + keytab["keytab file path"])
        remote.run("chmod "
                   + keytab["keytab file mode"]
                   + " " + keytab["keytab file path"])
    # Remove the intermediate files
    for intermediate_file in already_created:
        popen('rm -f ' + intermediate_file)
    # e) Check if everything works with the correct kinit command
    failed = []
    popen('kdestroy')
    for keytab in keytabs:
        if not len(keytab["keytab file path"]):
            continue
        remote = Remote(keytab["host"])
        try:
            identity = keytab["principal name"].split('@')[0]
            remote.run("su " + keytab["keytab file owner"] + " bash -c '/usr/bin/kinit -kt "
                       + keytab["keytab file path"] + " " + identity + "; kdestroy;'")
        except RuntimeError as e:
            failed.append((keytab, e))
    popen('kdestroy')
    if len(failed):
        for k, v in failed:
            print keytab["host"], k["principal name"], k["keytab file path"], e
        raise RuntimeError("Failed to create some keytabs! " + str(len(failed)) + "/" + str(len(keytabs)))
