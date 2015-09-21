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
Automated deployment library. Functions for interacting with any remote host and common shared functions useful in
deployment
"""
import commands
import subprocess as sub
import json
import os
import sys
import time
import re
#
# use for configuration
#

known_dest_types = ["workstation", "node"]
debug = True
# whether to turn off ssl checking if a proxy is detected
no_ssl_over_proxy = True
# whether the proxy blocks port 22
proxy_blocks_22 = True
# which port to ssh over when a proxy is discovered
proxy_port = 443
# warn about proxy
proxywarn = True
# strict host key checking
strict_host_key_checking = True
#
# General subprocess helper functions
#


def prLc(loc):
    """
    return project name from location of project
    """
    return loc.split('/')[-1].split('.')[0]


def htLc(loc):
    """
    return host name name from location of project
    """
    if loc.startswith('htt'):
        return loc.replace('//', '/').split('/')[1]
    elif loc.startswith("git@") or (loc.contains("@") and loc.contains(':')):
        return loc.split('@')[-1].split(':')[0]
    raise NameError('Could not interpret hostname of git repo ' + loc)


def detect_proxy():
    return ('http_proxy' in os.environ) and len(os.environ['http_proxy'])


def which(program):
    import os

    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def runQuiet(cmd, exit=True, shell=True):
    """
    Run a command, if this command fails raise a RuntimeError.
    Do not print the output of the command while it is running
    cmd: the command to run
    """
    cmdstr = ''
    if type(cmd) is list and len(cmd) > 1:
        cmdstr = ' '.join(cmd[:-1])
        if cmd[0] == 'ssh':
            cmdstr = cmdstr + " '" + cmd[-1] + "'"
        else:
            cmdstr = cmdstr + " " + cmd[-1]
    elif type(cmd) is list:
        cmdstr = cmd[0]
    else:
        cmdstr = cmd
    if debug:
        print cmdstr
    proc = sub.Popen(cmd, shell=shell, stdout=sub.PIPE, stderr=sub.PIPE)
    output, err = proc.communicate()
    status = proc.returncode
    if status and exit:
        raise RuntimeError("Problem running: \n" + cmdstr + "\n got:\n\t" + str(
            status) + "\n from stdout: \n" + output + " stderr: \n" + err)
    elif status:
        print >> sys.__stderr__, "ERROR: " + "Problem running: \n" + cmdstr + "\n got:\n\t" + str(
            status) + "\n from stdout: \n" + output + " stderr: \n" + err
    return output.strip()


def testproxy():
    """
    If you're over a proxy, better be able to use corkscrew for ssh
    """
    global proxywarn
    if detect_proxy():
        if not which("corkscrew"):
            raise SystemError("You must install corkscrew to ssh over a proxy")
        if proxywarn:
            print "Proxy detected, using port " + str(proxy_port) + " for ssh (some procedures will be impossible)"
            proxywarn = False
    return True


def proxopts(portop='-p'):
    if not detect_proxy():
        return []
    prnam = os.environ['http_proxy'].split('//')[-1].split(':')[0]
    prhs = os.environ['http_proxy'].split('//')[-1].split(':')[-1].split('/')[0]
    return [portop, str(proxy_port), '-o', 'UserKnownHostsFile=/dev/null', '-o', 'StrictHostKeyChecking=no', '-o',
            "ProxyCommand=corkscrew " + prnam + ' ' + prhs + ' %h %p']


def strictopts():
    if strict_host_key_checking:
        return []
    return ['-o', 'UserKnownHostsFile=/dev/null', '-o', 'StrictHostKeyChecking=no']


def mysleep(x):
    print "Sleeping", x * 10, "s"
    print "Z",
    for i in range(x):
        print "z",
        sys.__stdout__.flush()
        time.sleep(10)
    print "Z"
    sys.__stdout__.flush()


#
# Functions for contacting remote machines
#

class remoteHost(object):
    """
    A python class to hold functions applicable to a remote host

    self.user: the username
    self.host: the host ip or hostname or url
    self.access_key: the file holding the private access key

    Handles copying, remotely running commands and preparation for git
    """

    def __init__(self, user, host, access_key="~/.ssh/id_rsa"):
        if user is None or host is None or access_key is None:
            raise TypeError("None passed as argument to remoteHost" + str(user) + str(host) + str(access_key))
        self.user = user
        self.host = host
        self.gitprep = False
        self.github_key_local = ''
        self.github_key_remote = ''
        self.github_script_remote = ''
        global strict_host_key_checking
        self.strict = strict_host_key_checking
        if not os.path.exists(os.path.realpath(os.path.expanduser(access_key))):
            raise IOError("Key file does not exist! " + access_key)
        if "------" not in runQuiet("ls -l " + os.path.realpath(os.path.expanduser(access_key))):
            raise IOError("Your private keyfile " + access_key + " needs to have X00 permissions (400 or 600).")
        self.access_key = os.path.realpath(os.path.expanduser(access_key))

    def register(self):
        """
        Add remote key to list of known hosts
        """
        if not self.strict:
            return
        # try to prevent filesystem collisions with random 50-->500ms wait ...
        from random import randint
        from time import sleep

        sleep(0.005 * float(randint(10, 100)))
        if detect_proxy() and proxy_blocks_22:
            print "Warning, can't do ssh-keyscan over proxy which blocks port 22, skipping host key checks"
        runQuiet("ssh-keyscan -H " + self.host + " >> ~/.ssh/known_hosts ")
        runQuiet("ssh-keygen -R " + self.host)
        runQuiet("ssh-keyscan -H " + self.host + " >> ~/.ssh/known_hosts ")
        return

    def sshcmd(self, extrasshopts=[]):
        """
        internal function used for constructing ssh contact
        """
        return ["ssh"] + proxopts() + strictopts() + extrasshopts + ["-i", os.path.expanduser(self.access_key),
                                                                     self.user + "@" + self.host]

    def run(self, cmd, extrasshopts=[], exit=True):
        """
        run a command through ssh
        """
        cmd = cmd.strip()
        return runQuiet(self.sshcmd(extrasshopts) + [cmd], exit=exit, shell=False)

    def describe(self):
        """
        describe what to do to contact this machine
        """
        print "connect remotely with:"
        print ' '.join(self.sshcmd())

    def cp(self, local, remote):
        """
        Copy file or directory to the remote machine through scp
        """
        if not os.path.exists(os.path.realpath(os.path.expanduser(local))):
            raise IOError("file to copy must exist " + local)
        directory = os.path.isdir(os.path.realpath(os.path.expanduser(local)))
        propts = proxopts("-P")
        if len(propts):
            propts = ' '.join(propts[:-1]) + " '" + propts[-1] + "'"
        else:
            propts = ""
        cmd = "scp " + ' '.join(propts) + " " + ' '.join(
            strictopts()) + " -i " + self.access_key + " " + local + " " + self.user + "@" + self.host + ":" + remote
        if directory:
            cmd = cmd.replace(" -i ", " -r -i ")
        return runQuiet(cmd)

    def pull(self, local, remote):
        """
        Copy file or directory from the remote machine through scp
        """
        propts = proxopts("-P")
        if len(propts):
            propts = ' '.join(propts[:-1]) + " '" + propts[-1] + "'"
        else:
            propts = ""
        cmd = "scp " + propts + " " + ' '.join(
            strictopts()) + " -r -i " + self.access_key + " " + self.user + "@" + self.host + ":" + remote + " " + local
        return runQuiet(cmd)

    def check(self, firsttime=False):
        """
        verify if I can access this host. If firsttime=True i will temporarily ignore the known_hosts file
        """
        extrasshopts = []
        if firsttime:
            extrasshopts = ["-o", "UserKnownHostsFile=/dev/null", "-o", "StrictHostKeyChecking=no", "-o",
                            "PasswordAuthentication=no", "-o", "ConnectTimeout=1"]
        out = self.run("echo Hello World from $HOSTNAME", extrasshopts=extrasshopts)
        print out
        if "Hello World" not in out or "HOSTNAME" in out:
            raise ValueError(
                "Unable to contact machine " + self.user + "@" + self.host + "! or machine did not respond correctly")
        return True

    def detectLinuxVersion(self):
        """
        Which flavour of linux is running?
        """
        # first look into the redhat release
        def find_return(output):
            if "centos" in output.lower() and "release 6" in output.lower():
                return "Centos6"
            elif "centos" in output.lower() and "release 7" in output.lower():
                return "Centos7"
            elif "Ubuntu" in output:
                return "Ubuntu"
            return None

        # try commands first...
        for cmd in ["cat /etc/redhat-release", "lsb_release -a"]:
            try:
                output = self.run(cmd)
                v = find_return(output)
                if v:
                    return v
            except RuntimeError:
                pass
        # then try running uname
        output = self.run("uname -r")
        if "el6" in output:
            return "Centos6"
        elif "el7" in output:
            return "Centos7"
        raise SystemError("Cannot detect linux version, meaning this is not a compatible version")

    def prepGit(self, github_key_local, force=False, git_origin="git@gitlab-nl.dna.kpmglab.com"):
        """
        prepare the destination to be able to git clone
        """
        # hardcoded because of need to use gitwrap.sh, not exactly 100% secure...
        github_key_remote = "~/.rnadgithubnothingtoseehere"
        if self.gitprep and not force:
            return True
        if not os.path.exists(os.path.realpath(os.path.expanduser(github_key_local))):
            raise IOError("git keyfile must exist " + github_key_local)
        if force:
            self.run("rm -f " + github_key_remote)
        self.cp(os.path.realpath(os.path.expanduser(github_key_local)), github_key_remote)
        self.cp(os.path.realpath(os.path.dirname(__file__)) + "/../remotescripts/gitwrap.sh", "~/gitwrap.sh")
        self.github_script_remote = self.run("pwd") + "/gitwrap.sh"
        self.run("chmod 600 " + github_key_remote)
        self.run("chmod a+x ~/gitwrap.sh")
        try:
            ver = self.detectLinuxVersion()
            try:
                if ver.startswith("Centos"):
                    self.run("yum -y install git ")
                else:
                    self.run("apt-get -y install git")
            except RuntimeError:
                # back off and retry once, ABK-207
                import time

                time.sleep(5)
                if ver.startswith("Centos"):
                    self.run("yum -y install git ")
                else:
                    self.run("apt-get -y install git")
        except SystemError:
            print "Could not detect linux version, assuming git already installed"
        self.run("ssh-keyscan -H " + htLc(git_origin) + " >> ~/.ssh/known_hosts")
        self.run("ssh-keygen -R " + htLc(git_origin) + " ")
        self.run("ssh-keyscan -H " + htLc(git_origin) + " >> ~/.ssh/known_hosts")
        self.gitprep = True
        self.github_key_local = github_key_local
        self.github_key_remote = github_key_remote

    def git(self, cmd):
        """
        Run a git command remotely
        """
        if not self.gitprep:
            raise RuntimeError("host must be prepared with the github access key and gitwrap, run prepGit first")
        cmd = cmd.replace("'", "\'")
        out = self.run(
            "bash -c 'export GIT_SSH=" + self.github_script_remote + " ; env | grep GIT_SSH; git " + cmd + " '")

    def cleanGit(self):
        self.gitprep = False
        self.run('rm -f ' + self.github_key_remote)
        self.run('rm -f ~/gitwrap.sh')
        self.github_key_local = ''
        self.github_key_remote = ''
        self.github_script_remote = ''


#
# Specific deployment functions which take remotes as argument
#
class multiremotes(object):
    """
    Simple wrapper around pdsh
    Local machine must have passwordless access under same user to remote machines
    """

    def __init__(self, list_of_hosts, jump=None, access_key="~/.ssh/id_rsa"):
        """
        list_of_hosts is the name of all the machines I expect to be able to contact with passwordless access
        via should be a remotehost object where these commands run, or else they will be run locally,
        assuming passwordless access
        Sat jump if going through a intermediate jump box, otherwise set access_key if not id_rsa
        """
        self.hosts = list_of_hosts
        self.jump = jump
        global strict_host_key_checking
        self.strict = strict_host_key_checking
        if jump is None:
            if not os.path.exists(os.path.realpath(os.path.expanduser(access_key))):
                raise IOError("Key file does not exist! " + access_key)
            if "------" not in runQuiet("ls -l " + os.path.realpath(os.path.expanduser(access_key))):
                raise IOError("Your private keyfile " + access_key + " needs to have X00 permissions (400 or 600).")
            self.access_key = os.path.realpath(os.path.expanduser(access_key))

    def register(self):
        """
        Register keys to list of remotes
        """
        if self.jump is None:
            for host in self.hosts:
                remote = remoteHost("root", host)
                remote.register()
            return
        self.jump.register()
        # register remotes anyway, even though the strict checking is none for the local machine!
        for host in self.hosts:
            self.jump.run("ssh-keyscan -H " + host + " >> ~/.ssh/known_hosts")
            self.jump.run("ssh-keygen -R " + host + "")
            self.jump.run("ssh-keyscan -H " + host + " >> ~/.ssh/known_hosts")
        return

    def check(self, firsttime=False):
        """
        Verify keyless access to all destinations
        """
        # if there's no jump, I need keyless access from here
        if self.jump is None:
            for host in self.hosts:
                remote = remoteHost("root", host)
                remote.check(firsttime=firsttime)
            return True
        # if there is a jump, I need keyless access from there
        extrasshopts = []
        if firsttime:
            extrasshopts = ["-o", "UserKnownHostsFile=/dev/null", "-o", "StrictHostKeyChecking=no", "-o",
                            "PasswordAuthentication=no", "-o", "ConnectTimeout=1"]
        for host in self.hosts:
            out = self.jump.run(
                "ssh " + ' '.join(extrasshopts) + " root@" + host + " echo Hello World from \\$HOSTNAME",
                extrasshopts=extrasshopts)
            print out
            if "Hello World" not in out or "HOSTNAME" in out:
                raise ValueError("Unable to contact machine root@" + host + "! or machine did not respond correctly")
            return True

    def run(self, cmd, exit=True):
        """
        Run command on all remote machines, either starting locally or starting on some remote jump server
        """
        if self.jump is None:
            excmd = ""
            if detect_proxy():
                propts = proxopts()
                propts = " ".join(propts[:-1]) + '"' + propts[-1] + '"'
                excmd = "export PDSH_SSH_ARGS_APPEND='" + propts + " " + ' '.join(
                    strictopts()) + " -i " + self.access_key + "'; "
            elif not self.strict:
                excmd = "export PDSH_SSH_ARGS_APPEND=' " + ' '.join(strictopts()) + " -i " + self.access_key + " '; "
            else:
                excmd = "export PDSH_SSH_ARGS_APPEND=' -i " + self.access_key + " '; "
            return runQuiet(excmd + "pdsh -S -w " + ','.join(self.hosts) + " -R ssh " + cmd, exit=exit)
        else:
            return self.jump.run("pdsh -S -w " + ','.join(self.hosts) + " -R ssh " + cmd, exit=exit)

    def cp(self, localfile, remotefile):
        """
        use scp, one at a time, unfortunately :S, either starting locally or starting on some remote jump server
        """
        directory = os.path.isdir(os.path.realpath(os.path.expanduser(localfile)))
        for host in self.hosts:
            if self.jump is None:
                remote = remoteHost("root", host, self.access_key)
                remote.cp(localfile, remotefile)
                return
            else:
                self.jump.cp(localfile, remotefile)
                cmd = 'scp '
                if directory:
                    cmd = cmd + '-r '
                self.jump.run(cmd + remotefile + " " + host + ":" + remotefile)


# @TODO: Consolidate the two methods below!

def _addtoolboxtoremote(remote, github_key_location, git_origin, dest_type="workstation",
                        toolbox_proj=None, branch="", background=True):
    """
    Add the KaveToolbox once a remote connection is established
    """
    if not os.path.exists(os.path.expanduser(github_key_location)):
        raise IOError("Your git access key must exist " + github_key_location)
    if dest_type not in known_dest_types:
        raise ValueError("dest_type can only be one of: " + known_dest_types.__str__() + " you asked for " + dest_type)
    if toolbox_proj is None:
        if "kavetoolbox" in git_origin.lower() and git_origin.startswith("git@"):
            toolbox_proj = git_origin.split(':')[-1]
        elif "github" in git_origin:
            toolbox_proj = "KaveIO/KaveToolbox.git"
        elif "gitlab-nl" in git_origin:
            toolbox_proj = "kave/kavetoolbox.git"
        elif "ambarikave.git" in git_origin.lower():
            toolbox_proj = git_origin.split(':')[-1].replace("AmbariKave.git",
                                                             "KaveToolbox.git"
                                                             ).replace("ambarikave.git", "kavetoolbox.git")
        else:
            raise NameError("Cannot guess the toolbox project name from " + git_origin)
    remote.check()
    installcmd = "./" + prLc(toolbox_proj) + '/scripts/KaveInstall --quiet'
    if dest_type == "workstation":
        # default at the moment
        installcmd = installcmd
    elif dest_type == "node":
        # add the --node flag
        installcmd = installcmd + " --node"
    # remote.run("rm -rf "+prLc(toolbox_proj))
    remote.prepGit(github_key_location)
    br = ""
    if len(branch) and branch != "HEAD" and branch != "head" and branch != "master":
        br = "-b " + branch
    remote.git("clone " + br + " " + git_origin.split(':')[0] + ":" + toolbox_proj)
    if not background:
        remote.run(installcmd)
    else:
        remote.run("nohup " + installcmd + " < /dev/null > inst.stdout 2> inst.stderr &")
        print "installing toolbox in background process (check before bringing down the machine)"
        # remote.cleanGit()


def _addambaritoremote(remote, github_key_location, git_origin, branch="", background=True):
    """
    Add our ambari to a remote machine
    """
    remote.run("service iptables stop")
    remote.run("chkconfig iptables off")
    if not os.path.exists(os.path.expanduser(github_key_location)):
        raise IOError("Your git access key must exist " + github_key_location)
    remote.prepGit(github_key_location)
    br = ""
    if len(branch) and branch != "HEAD" and branch != "head" and branch != "master":
        br = "-b " + branch
    remote.git("clone " + br + " " + git_origin)
    installcmd = "bash -c \"" + prLc(git_origin) + "/dev/install.sh; " + prLc(
        git_origin) + "/dev/patch.sh; ambari-server start\""
    if not background:
        remote.run(installcmd)
    else:
        remote.run("nohup " + installcmd + " < /dev/null > inst.stdout 2> inst.stderr &")
        print "installing ambari in background process (check before bringing down the machine)"


# @TODO: Implement the local functionality!
# @TODO: Consolidate the repo functionality from kavecommon!
def deployOurSoft(remote, version="latest", git=False, gitenv=None, pack="ambarikave",
                  repo="http://repos:kaverepos@repos.kave.io", background=True, options=""):
    """
    Add ambari or KaveToolbox to a remote machine.
    version=version to deploy, branch or 'HEAD' for git, 'local' to package locally and copy
    git=False, True imples perform checkout from git, which needs to know an ssh key and an origin
    gitenv: {"KeyFile":"/path/to/private/key","Origin":"git@github.com"}
    pack: which package to deploy, ambarikave or kavetoolbox?
    repo: where to get the package from if downloading it?
    background=True: install in background process?
    options="": what options to pass to the installer?
    """
    if version == "local" and pack.lower() != "ambarikave":
        raise ValueError("Don't know how to locally package " + pack)
    if version == "latest" and git:
        version = "master"
    if version == "latest":
        version = "1.3-Beta"
    if (version == "HEAD" or version == "master") and (not git or gitenv is None):
        raise ValueError("master and HEAD imply a git checkout, but you didn't ask to use git!")
    if version == "local" and git:
        raise ValueError("deploy from local does not make sense when you've specified to also use git!")
    if pack.lower() not in ["ambarikave", "kavetoolbox"]:
        raise ValueError("Unknown package " + pack + " I knew " + ["ambarikave", "kavetoolbox"].__str())
    pack = pack.lower()
    remote.check()
    # get directly from repo
    if not git:
        remote.run("yum -y install wget curl")
        arch = "centos6"
        dir = "AmbariKave"
        dfile = pack + "-installer-" + arch + "-" + version + ".sh"
        if pack == "kavetoolbox":
            arch = "noarch"
            dir = "KaveToolbox"
            dfile = pack + "-installer-" + version + ".sh"
        remote.run("wget " + repo + "/" + arch + "/" + dir + "/" + version + "/" + dfile)
        if not background:
            remote.run("bash " + dfile + " " + options)
            return
        else:
            remote.run("nohup bash " + dfile + " " + options + " < /dev/null > inst.stdout 2> inst.stderr &")
            print "installing " + pack + " in background process (check before bringing down the machine)"
            return
            # return True
    elif version == "local":
        raise ValueError("Local mode not implemented yet, sorry!")
    else:
        # extract info from git env
        github_key_location = gitenv["KeyFile"]
        git_origin = gitenv["Origin"]
        if pack == "ambarikave":
            _addambaritoremote(remote, github_key_location=github_key_location, git_origin=git_origin, branch=version,
                               background=background)
            return
        else:
            dest_type = "workstation"
            if "--node" in options:
                dest_type == "node"
            _addtoolboxtoremote(remote, github_key_location=github_key_location, dest_type=dest_type,
                                git_origin=git_origin, branch=version, background=background)
            return


def waitforambari(ambari):
    """
    Wait until ambari server is up and running, error if it doesn't appear!
    """
    import time
    # wait until ambari server is up
    rounds = 1
    flag = False
    while rounds <= 10:
        try:
            stdout = ambari.run("service iptables stop")
        except RuntimeError:
            pass
        try:
            stdout = ambari.run("curl --user admin:admin http://localhost:8080/api/v1/clusters")
            flag = True
            break
        except RuntimeError:
            pass
        time.sleep(60)
        rounds = rounds + 1
    if not flag:
        raise ValueError("ambari server not contactable after 10 minutes (" + ' '.join(ambari.sshcmd()) + ")")
    return True


def waitforrequest(ambari, clustername, request, timeout=10):
    """
    Wait until a certain request succeeds, error if it fails!
    """
    import time
    # wait until ambari server is up
    rounds = 1
    flag = False
    while rounds <= timeout:
        stdout = ambari.run(
            "curl --user admin:admin http://localhost:8080/api/v1/clusters/" + clustername + "/requests/" + str(
                request))
        if '"request_status" : "FAILED"' in stdout:
            raise ValueError("request from blueprint failed (" + ' '.join(ambari.sshcmd()) + ")")
        if '"request_status" : "COMPLETED"' in stdout:
            flag = True
            break
        time.sleep(60)
        rounds = rounds + 1
    if not flag:
        raise ValueError("request not complete after " + timeout + " minutes (" + ' '.join(ambari.sshcmd()) + ")")
    return True


def confremotessh(remote, port=443):
    """
    Open 443 and allow reverse tunnelling on gateway machines
    http://marcofalchi.blogspot.nl/2013/05/centos-64-redhat-64-fedora-18-change.html
    """
    # selinux tools
    remote.run("yum -y install policycoreutils-python")
    remote.run("semanage port -m -t ssh_port_t -p tcp " + str(port))
    # modify iptables
    remote.cp(os.path.dirname(__file__) + "/../remotescripts/add_incoming_port.py", "~/add_incoming_port.py")
    remote.run("python add_incoming_port.py " + str(port))
    # modify sshconfig
    remote.run("echo \"GatewayPorts clientspecified\" >> /etc/ssh/sshd_config")
    remote.run("echo \"Port 22\" >> /etc/ssh/sshd_config")
    remote.run("echo \"Port " + str(port) + "\" >> /etc/ssh/sshd_config")
    # restart services
    remote.run("/etc/init.d/sshd restart")
    import time

    time.sleep(5)
    remote.run("/etc/init.d/iptables restart")


def waitUntilUp(remote, max_wait):
    """
    Wait a little while for a machine to be contactable
    """
    try:
        return remote.check(firsttime=True)
    except RuntimeError, ValueError:
        pass
    up = False
    for i in range(max_wait):
        try:
            mysleep(10 - (i > 0) * 7)
            up = remote.check(firsttime=True)
            break
        except RuntimeError, ValueError:
            print "not ready yet, sleep again"
            pass
    if not up:
        raise SystemError(remote.host + " not contactable after 10 minutes")
    return True


def getsshid(remote, saveas, retry=0):
    """
    If the machine does not yet have an id_rsa.pub, then generate it
    Return the public key locally
    """
    output = remote.run("ls -al .ssh")
    if retry >= 3:
        raise RuntimeError("Did not manage to copy ssh key after three retries!")
    if "id_rsa.pub" not in output:
        remote.run("ssh-keygen -t rsa -f .ssh/id_rsa -P \"\"")
        remote.run("chmod 600 .ssh/id_rsa")
        return getsshid(remote, saveas, retry + 1)
    if not os.path.exists(saveas):
        remote.pull(saveas, "~/.ssh/id_rsa.pub")
    if not os.path.exists(saveas):
        return getsshid(remote, saveas, retry + 1)
    return


def configureKeyless(source, destination, dest_internal_ip=None, preservehostname=False):
    """
    Given two remote connections, configure the first to have keyless access to the second
    If the destination has an internal network ip from the source then it needs to be added separately
    preservehostname implies that the source knows the hostname of the destination ip
    """
    if dest_internal_ip is None:
        dest_internal_ip = destination.host
    localcopy = "/tmp/somepublickey" + destination.host
    if os.path.exists(localcopy):
        runQuiet("rm -rf " + localcopy)
    getsshid(source, localcopy)
    # copy public key
    destination.cp(localcopy, "~/.ssh/" + source.host + ".pub")
    if os.path.exists(localcopy):
        runQuiet("rm -rf " + localcopy)
    # append to authorized_keys
    destination.run("cat ~/.ssh/" + source.host + ".pub >> .ssh/authorized_keys")
    destination.run("cat ~/.ssh/" + source.host + ".pub >> .ssh/authorized_keys2")
    # ensure no prompt because of the silly not recognised host yhingy
    source.run("ssh-keyscan -H " + dest_internal_ip + " >> .ssh/known_hosts")
    source.run("ssh-keygen -R " + dest_internal_ip)
    source.run("ssh-keyscan -H " + dest_internal_ip + " >> .ssh/known_hosts")
    if preservehostname:
        hostname = destination.run("hostname -s")
        source.run("ssh-keyscan -H " + hostname + " >> .ssh/known_hosts")
        source.run("ssh-keygen -R " + hostname)
        source.run("ssh-keyscan -H " + hostname + " >> .ssh/known_hosts")
        hostname = destination.run("hostname")
        source.run("ssh-keyscan -H " + hostname + " >> .ssh/known_hosts")
        source.run("ssh-keygen -R " + hostname)
        source.run("ssh-keyscan -H " + hostname + " >> .ssh/known_hosts")
    # test access by trying a double-hopping ssh
    output = source.run("ssh " + destination.user + "@" + dest_internal_ip + " echo Hello friend from \\$HOSTNAME")
    if "friend" not in output or "HOST" in output:
        raise SystemError("Setting up keyless access failed!")
    if preservehostname:
        output = source.run("ssh " + destination.user + "@" + hostname + " echo Hello friend from \\$HOSTNAME")
        if "friend" not in output or "HOST" in output:
            raise SystemError("Setting up keyless access failed!")
    return True


def renameRemoteHost(remote, new_name, newdomain=None):
    """
    rename a remote host to new_name.
    If newdomain is given, also add the new domain, if not given, use localdomain
    """
    remote.cp(os.path.realpath(os.path.dirname(__file__)) + "/../remotescripts/rename_me.py", "~/rename_me.py")
    cmd = "python rename_me.py " + new_name
    if newdomain is not None:
        cmd = cmd + " " + newdomain
    remote.run(cmd)


def addAsHost(edit_remote, add_remote, dest_internal_ip=None, extra_domains=[]):  # ["localdomain"]):
    """
    will add 'ip hostname' of add_remote as a host shortcut in edit_remote

    add the hostname, the domain it thinks it is in, and any extra domains given in extra_domains
    """
    hostname = add_remote.run("hostname -s")
    try:
        dom = add_remote.run("hostname -d")
        if len(dom):
            extra_domains.append(dom)
    except RuntimeError:
        pass
    try:
        dom = add_remote.run("hostname")
        if "." in dom:
            dom = '.'.join(dom.split('.')[1:])
            extra_domains.append(dom)
    except RuntimeError:
        pass
    unique_domains = []
    for dom in extra_domains:
        if dom not in unique_domains:
            unique_domains.append(dom)
    no_dots = []
    all_domains = [hostname + "." + dom for dom in unique_domains] + [hostname]
    no_dots = [n for n in all_domains if '.' not in n]
    fq = [f for f in all_domains if '.' in f and 'localdomain' not in f]
    rest = [r for r in all_domains if r not in fq and r not in no_dots]
    all_domains = " ".join(fq + rest + no_dots)
    if dest_internal_ip is None:
        dest_internal_ip = add_remote.host
    # first remove this host if it is already defined ...
    edit_remote.run("grep -v '" + dest_internal_ip + "' /etc/hosts | grep -v '" + hostname + "' > tmpfile ")
    edit_remote.run("mv -f tmpfile /etc/hosts")
    edit_remote.run("echo '" + dest_internal_ip + " " + all_domains + "' >> /etc/hosts")
