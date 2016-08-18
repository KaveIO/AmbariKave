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


def pr_lc(loc):
    """
    return project name from location of project
    """
    return loc.split('/')[-1].split('.')[0]


def ht_lc(loc):
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


class ShellExecuteError(RuntimeError):
    """
    Runtime errors when calling commands in this module
    """
    pass


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


def run_quiet(cmd, exit=True, shell=True):
    """
    Run a command, if this command fails raise a ShellExecuteError.
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
        raise ShellExecuteError("Problem running: \n" + cmdstr + "\n got:\n\t" + str(
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


def parse_rhrelease(output):
    """
    Take a string and return a linux flavor
    """
    if "centos" in output.lower() and "release 6" in output.lower():
        return "Centos6"
    elif "centos" in output.lower() and "release 7" in output.lower():
        return "Centos7"
    elif "Ubuntu" in output:
        return "Ubuntu"
    return None


def parse_uname(output):
    if "el6" in output:
        return "Centos6"
    if "el7" in output:
        return "Centos7"
    return None


def request_session(retries=5, backoff_factor=0.1, status_forcelist=[500, 501, 502, 503, 504, 401, 404]):
    import requests
    from requests.packages.urllib3.util.retry import Retry
    from requests.adapters import HTTPAdapter
    s = requests.Session()
    retries = Retry(total=retries,
                    backoff_factor=backoff_factor,
                    status_forcelist=status_forcelist)
    s.mount('http://', HTTPAdapter(max_retries=retries))
    s.mount('https://', HTTPAdapter(max_retries=retries))
    return s


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
        if "------" not in run_quiet("ls -l " + os.path.realpath(os.path.expanduser(access_key))):
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
        run_quiet("ssh-keyscan -H " + self.host + " >> ~/.ssh/known_hosts ")
        run_quiet("ssh-keygen -R " + self.host)
        run_quiet("ssh-keyscan -H " + self.host + " >> ~/.ssh/known_hosts ")
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
        return run_quiet(self.sshcmd(extrasshopts) + [cmd], exit=exit, shell=False)

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
        return run_quiet(cmd)

    def pull(self, local, remote):
        """
        Copy file or directory from the remote machine through scp
        """
        propts = proxopts("-P")
        if len(propts):
            propts = ' '.join(propts[:-1]) + " '" + propts[-1] + "'"
        else:
            propts = ""
        cmd = ("scp " + propts + " " + ' '.join(strictopts())
               + " -r -i " + self.access_key + " " + self.user + "@"
               + self.host + ":" + remote + " " + local
               )
        return run_quiet(cmd)

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

    def detect_linux_version(self):
        """
        Which flavour of linux is running?
        """

        # try commands first...
        for cmd in ["cat /etc/redhat-release", "lsb_release -a"]:
            try:
                output = self.run(cmd)
                v = parse_rhrelease(output)
                if v:
                    return v
            except ShellExecuteError:
                pass
        # then try running uname
        output = self.run("uname -r")
        el = parse_uname(output)
        if el:
            return el
        raise SystemError("Cannot detect linux version, meaning this is not a compatible version")

    def prep_git(self, github_key_local, force=False, git_origin="git@gitlab-nl.dna.kpmglab.com"):
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
            ver = self.detect_linux_version()
            try:
                if ver.startswith("Centos"):
                    self.run("yum -y install git ")
                else:
                    self.run("apt-get -y install git")
            except ShellExecuteError:
                # back off and retry once, ABK-207
                import time

                time.sleep(5)
                if ver.startswith("Centos"):
                    self.run("yum -y install git ")
                else:
                    self.run("apt-get -y install git")
        except SystemError:
            print "Could not detect linux version, assuming git already installed"
        self.run("ssh-keyscan -H " + ht_lc(git_origin) + " >> ~/.ssh/known_hosts")
        self.run("ssh-keygen -R " + ht_lc(git_origin) + " ")
        self.run("ssh-keyscan -H " + ht_lc(git_origin) + " >> ~/.ssh/known_hosts")
        self.gitprep = True
        self.github_key_local = github_key_local
        self.github_key_remote = github_key_remote

    def git(self, cmd):
        """
        Run a git command remotely
        """
        if not self.gitprep:
            raise RuntimeError("host must be prepared with the github access key and gitwrap, run prep_git first")
        cmd = cmd.replace("'", "\'")
        out = self.run(
            "bash -c 'export GIT_SSH=" + self.github_script_remote + " ; env | grep GIT_SSH; git " + cmd + " '")

    def clean_git(self):
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
            if "------" not in run_quiet("ls -l " + os.path.realpath(os.path.expanduser(access_key))):
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

    def detect_linux_version(self):
        """
        Which flavour of linux is running?
        """

        # try commands first...
        vs = []
        for cmd in ["cat /etc/redhat-release", "lsb_release -a"]:
            try:
                output = self.run(cmd)
            except ShellExecuteError:
                continue
            vs = [parse_rhrelease(o) for o in output.split('\n')]
        # then try running uname
        try:
            output = self.run("uname -r")
            nvs = [parse_uname(o) for o in output.split('\n')]
        except ShellExecuteError:
            nvs = []

        versions = vs + nvs
        versions = [v for v in versions if v is not None]
        versions = set(versions)
        if not len(versions):
            raise SystemError("Cannot detect linux version, meaning this is not a compatible version")
        if len(versions) == 1:
            return list(versions)[0]
        return versions

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
            return run_quiet(excmd + "pdsh -S -w " + ','.join(self.hosts) + " -R ssh " + cmd, exit=exit)
        else:
            return self.jump.run("pdsh -S -w " + ','.join(self.hosts) + " -R ssh " + cmd, exit=exit)

    def cp(self, localfile, remotefile):
        """
        Use pdcp if it exists, else use scp one-at-a-time
        """
        directory = os.path.isdir(os.path.realpath(os.path.expanduser(localfile)))

        # first detect if I am able to use pdcp or not

        pdcp = False
        if self.jump is None and which('pdcp'):
            # local pdcp
            pdcp = True

        if self.jump is not None:
            try:
                # remote pdcp
                self.jump.run('which pdcp')
                pdcp = True
            except ShellExecuteError:
                pdcp = False

        excmd = ""

        if self.jump is not None:
            self.jump.cp(localfile, remotefile)
            localfile = remotefile

        diropt = ''

        if directory:
            diropt = ' -r '

        if pdcp:
            excmd = 'export PDSH_SSH_ARGS_APPEND=" '
            if self.jump is None:
                excmd = excmd + " -i " + self.access_key

            if detect_proxy():
                propts = proxopts()
                propts = " ".join(propts[:-1]) + '\\"' + propts[-1] + '\\"'
                excmd = excmd + " " + propts + " " + ' '.join(strictopts())
            elif not self.strict:
                excmd = excmd + " " + ' '.join(strictopts())
            excmd = excmd + '"; '

            if self.jump is None:
                run_quiet(excmd + "pdcp -w " + diropt + ','.join(self.hosts)
                          + " " + localfile + " " + remotefile, exit=exit)
            else:
                self.jump.run(excmd + "pdcp -w " + diropt + ','.join(self.hosts)
                              + " " + localfile + " " + remotefile, exit=exit)
        else:
            for host in self.hosts:
                if self.jump is None:
                    remote = remoteHost("root", host, self.access_key)
                    remote.cp(localfile, remotefile)
                    return
                else:
                    if host != self.jump.user + '@' + self.jump.host:
                        self.jump.run('scp ' + diropt + remotefile + " " + host + ":" + remotefile)


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
    installcmd = "./" + pr_lc(toolbox_proj) + '/scripts/KaveInstall --quiet'
    if dest_type == "workstation":
        # default at the moment
        installcmd = installcmd
    elif dest_type == "node":
        # add the --node flag
        installcmd = installcmd + " --node"
    # remote.run("rm -rf "+pr_lc(toolbox_proj))
    remote.prep_git(github_key_location)
    br = ""
    if len(branch) and branch != "HEAD" and branch != "head" and branch != "master":
        br = "-b " + branch
    remote.git("clone " + br + " " + git_origin.split(':')[0] + ":" + toolbox_proj)
    if not background:
        remote.run(installcmd)
    else:
        remote.run("nohup " + installcmd + " < /dev/null > inst.stdout 2> inst.stderr &")
        print "installing toolbox in background process (check before bringing down the machine)"
        # remote.clean_git()


def _addambaritoremote(remote, github_key_location, git_origin, branch="", background=True):
    """
    Add our ambari to a remote machine
    """
    # ignore failures here for now, since iptables does not exist on centos7
    try:
        remote.run("service iptables stop")
        remote.run("chkconfig iptables off")
    except ShellExecuteError:
        pass
    if not os.path.exists(os.path.expanduser(github_key_location)):
        raise IOError("Your git access key must exist " + github_key_location)
    remote.prep_git(github_key_location)
    br = ""
    if len(branch) and branch != "HEAD" and branch != "head" and branch != "master":
        br = "-b " + branch
    remote.git("clone " + br + " " + git_origin)
    installcmd = "bash -c \"" + pr_lc(git_origin) + "/dev/install.sh; " + pr_lc(
        git_origin) + "/dev/patch.sh; ambari-server start\""
    if not background:
        remote.run(installcmd)
    else:
        remote.run("nohup " + installcmd + " < /dev/null > inst.stdout 2> inst.stderr &")
        print "installing ambari in background process (check before bringing down the machine)"


# @TODO: Implement the local functionality!
# @TODO: Consolidate the repo functionality from kavecommon!
def deploy_our_soft(remote, version="latest", git=False, gitenv=None, pack="ambarikave",
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
        version = "2.2-Beta-Pre"
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
            _addambaritoremote(remote, github_key_location=github_key_location,
                               git_origin=git_origin, branch=version,
                               background=background)
            return
        else:
            dest_type = "workstation"
            if "--node" in options:
                dest_type == "node"
            _addtoolboxtoremote(remote, github_key_location=github_key_location, dest_type=dest_type,
                                git_origin=git_origin, branch=version, background=background)
            return


def wait_for_ambari(ambari, maxrounds=10, check_inst=None):
    """
    Wait until ambari server is up and running, error if it doesn't appear!
    Also check if a list of files, e.g. inst.stdout or inst.stderr contains errors
    """
    import time
    # wait until ambari server is up
    rounds = 1
    flag = False
    ambari.cp(os.path.realpath(os.path.dirname(__file__))
              + "/../remotescripts/default.netrc",
              "~/.netrc")
    while rounds <= maxrounds:
        # ignore failures here for now, since iptables does not exist on centos7
        try:
            # modify iptables, only in case of Centos6
            if ambari.detect_linux_version() in ["Centos6"]:
                ambari.run("service iptables stop")
        except ShellExecuteError:
            pass
        # check file pointed to for failures
        try:
            if check_inst:
                for afile in check_inst:
                    cat = ambari.run("cat " + afile).strip().lower()
                    # ignore errors with mirrors
                    cat = cat.replace("[Errno 14] HTTP Error 404 - Not Found".lower(), '')
                    cat = cat.replace("[Errno 14] HTTP Error 503 - Service Unavailable".lower(), '')
                    if "error" in cat or "exception" in cat or "failed" in cat:
                        raise SystemError("Failure in ambari server start server detected!")
        except ShellExecuteError:
            pass

        try:
            stdout = ambari.run("curl --retry 5 --netrc http://localhost:8080/api/v1/clusters")
            flag = True
            break
        except ShellExecuteError:
            pass
        time.sleep(60)
        rounds = rounds + 1
    if not flag:
        raise IOError("ambari server not contactable after 10 minutes (" + ' '.join(ambari.sshcmd()) + ")")
    return True


def waitforrequest(ambari, clustername, request, timeout=10):
    """
    Wait until a certain request succeeds, error if it fails!
    """
    import time
    # wait until ambari server is up
    rounds = 1
    flag = False
    ambari.cp(os.path.realpath(os.path.dirname(__file__))
              + "/../remotescripts/default.netrc",
              "~/.netrc")
    while rounds <= timeout:
        cmd = ("curl --retry 5 --netrc http://localhost:8080/api/v1/clusters/"
               + clustername + "/requests/" + str(request))
        # If this fails, wait a second and try again, then really fail
        try:
            stdout = ambari.run(cmd)
        except ShellExecuteError:
            time.sleep(3)
            stdout = ambari.run(cmd)
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
    # modify iptables, only in case of Centos6
    if remote.detect_linux_version() in ["Centos6"]:
        remote.cp(os.path.dirname(__file__) + "/../remotescripts/add_incoming_port.py", "~/add_incoming_port.py")
        remote.run("python add_incoming_port.py " + str(port))
    # modify sshconfig
    pre = ''
    if hasattr(remote, 'hosts'):
        pre = '"'
    remote.run(pre + "echo >> /etc/ssh/sshd_config" + pre)
    remote.run(pre + "echo \"GatewayPorts clientspecified\" >> /etc/ssh/sshd_config" + pre)
    remote.run(pre + "echo \"Port 22\" >> /etc/ssh/sshd_config" + pre)
    remote.run(pre + "echo \"Port " + str(port) + "\" >> /etc/ssh/sshd_config" + pre)
    # restart services
    try:
        remote.run("service sshd restart")
    except ShellExecuteError:
        remote.run("service ssh restart")
    import time
    time.sleep(2)
    # modify iptables, only in case of Centos6
    if remote.detect_linux_version() in ["Centos6"]:
        remote.run("service iptables restart")
        time.sleep(1)
    try:
        remote.run("service sshd restart")
    except ShellExecuteError:
        remote.run("service ssh restart")


def confallssh(remote, restart=True):
    """
    Common sshd_config for all machines upped with these scripts
    Forbid weak ssh encryption
    """
    remote.run("bash -c 'echo >> /etc/ssh/sshd_config'")
    remote.run("bash -c 'echo \"Ciphers aes128-ctr,aes192-ctr,aes256-ctr,arcfour256,arcfour128\" "
               + " >> /etc/ssh/sshd_config'")
    remote.run("bash -c 'echo \"MACs hmac-sha1,umac-64@openssh.com,hmac-ripemd160\" >> /etc/ssh/sshd_config'")
    if restart:
        try:
            remote.run("service sshd restart")
        except ShellExecuteError:
            remote.run("service ssh restart")
        import time
        time.sleep(2)


def wait_until_up(remote, max_wait):
    """
    Wait a little while for a machine to be contactable
    """
    try:
        return remote.check(firsttime=True)
    except ShellExecuteError, ValueError:
        pass
    up = False
    for i in range(max_wait):
        try:
            mysleep(10 - (i > 0) * 7)
            up = remote.check(firsttime=True)
            break
        except ShellExecuteError, ValueError:
            print "not ready yet, sleep again"
            pass
    if not up:
        raise SystemError(remote.host + " not contactable after 10 minutes")
    return True


def remote_cp_authkeys(remote, user2='root'):
    """
    Copy authorized_keys from one user to another on remote machine
    return new remote with the new user
    """
    remote.check()
    if remote.user == user2:
        return remote
    hdir = '/home/' + remote.user
    if remote.user == 'root':
        hdir = '/root'
    hdir2 = '/home/' + user2
    if user2 == 'root':
        hdir2 = '/root'
    remote.run('sudo -u ' + user2 + " cp " + hdir + "/.ssh/authorized_keys "
               + hdir2 + "/.ssh/", extrasshopts=['-t', '-t'])
    remote2 = remoteHost(user2, remote.host, remote.access_key)
    return remote2


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


def configure_keyless(source, destination, dest_internal_ip=None, preservehostname=False):
    """
    Given two remote connections, configure the first to have keyless access to the second
    If the destination has an internal network ip from the source then it needs to be added separately
    preservehostname implies that the source knows the hostname of the destination ip
    """
    if dest_internal_ip is None:
        dest_internal_ip = destination.host
    localcopy = "/tmp/somepublickey" + destination.host
    if os.path.exists(localcopy):
        run_quiet("rm -rf " + localcopy)
    getsshid(source, localcopy)
    # copy public key
    destination.cp(localcopy, "~/.ssh/" + source.host + ".pub")
    if os.path.exists(localcopy):
        run_quiet("rm -rf " + localcopy)
    # append to authorized_keys
    destination.run("cat ~/.ssh/" + source.host + ".pub >> .ssh/authorized_keys")
    destination.run("cat ~/.ssh/" + source.host + ".pub >> .ssh/authorized_keys2")
    # ensure no prompt because of the silly not recognised host thingy

    def scan_and_store_key(remote, host_to_scan):
        """
        Uses ssh-keyscan to detemine key of host, and then without fail
        replaces entries for this host in the known_hosts file
        """
        remote.run("ssh-keyscan -H " + host_to_scan + " >> .ssh/known_hosts")
        remote.run("ssh-keygen -R " + host_to_scan)
        remote.run("ssh-keyscan -H " + host_to_scan + " >> .ssh/known_hosts")
        if host_to_scan != host_to_scan.lower():
            scan_and_store_key(remote, host_to_scan.lower())

    scan_and_store_key(source, dest_internal_ip)
    if preservehostname:
        scan_and_store_key(source, destination.run("hostname -s"))
        scan_and_store_key(source, destination.run("hostname"))
    # test access by trying a double-hopping ssh
    output = source.run("ssh " + destination.user + "@" + dest_internal_ip + " echo Hello friend from \\$HOSTNAME")
    # will fail if the machine has the work HOST in the name, or could give false positive
    # if the local machine has the word friend in the name
    if "friend" not in output or "HOST" in output:
        raise SystemError("Setting up keyless access failed!")
    if preservehostname:
        output = source.run("ssh " + destination.user + "@" + destination.run("hostname")
                            + " echo Hello friend from \\$HOSTNAME")
        if "friend" not in output or "HOST" in output:
            raise SystemError("Setting up keyless access failed!")
    return True


def rename_remote_host(remote, new_name, newdomain=None, skip_cp=False):
    """
    rename a remote host to new_name.
    If newdomain is given, also add the new domain, if not given, use localdomain
    """
    if not skip_cp:
        remote.cp(os.path.realpath(os.path.dirname(__file__)) + "/../remotescripts/rename_me.py", "~/rename_me.py")
    cmd = "python rename_me.py " + new_name.lower()
    if newdomain is not None:
        cmd = cmd + " " + newdomain.lower()
    remote.run(cmd)


def rename_remote_hosts(remotes_to_name, newdomain=None):
    """
    rename several remote hosts to new_name.
    If newdomain is given, also add the new domain, if not given, use localdomain
    """
    remotes = remotes_to_name.keys()
    mremotes = ["ssh:root@" + remote.host for remote in remotes]
    mremotes = multiremotes(list_of_hosts=mremotes, access_key=remotes[0].access_key)
    mremotes.cp(os.path.realpath(os.path.dirname(__file__)) + "/../remotescripts/rename_me.py", "rename_me.py")
    for remote, name in remotes_to_name.iteritems():
        rename_remote_host(remote, name, newdomain, skip_cp=True)


def add_as_host(edit_remote, add_remote, dest_internal_ip=None, extra_domains=[]):  # ["localdomain"]):
    """
    will add 'ip hostname' of add_remote as a host shortcut in edit_remote

    add the hostname, the domain it thinks it is in, and any extra domains given in extra_domains
    """
    hostname = add_remote.run("hostname -s")
    try:
        dom = add_remote.run("hostname -d")
        if len(dom):
            extra_domains.append(dom)
    except ShellExecuteError:
        pass
    try:
        dom = add_remote.run("hostname")
        if "." in dom:
            dom = '.'.join(dom.split('.')[1:])
            extra_domains.append(dom)
    except ShellExecuteError:
        pass
    unique_domains = []
    for dom in extra_domains:
        if dom not in unique_domains:
            unique_domains.append(dom)

    all_domains = [hostname + "." + dom for dom in unique_domains] + [hostname]
    no_dots = [n for n in all_domains if '.' not in n]
    fq = [f for f in all_domains if '.' in f and 'localdomain' not in f]
    rest = [r for r in all_domains if r not in fq and r not in no_dots]
    all_domains = " ".join(fq + rest + no_dots)
    if dest_internal_ip is None:
        dest_internal_ip = add_remote.host
    # first remove this host if it is already defined ...
    pre = ''
    if hasattr(edit_remote, 'hosts'):
        pre = '"'
    edit_remote.run(pre + "grep -v '" + dest_internal_ip + "' /etc/hosts | grep -v '" + hostname + "' > tmpfile " + pre)
    edit_remote.run("mv -f tmpfile /etc/hosts")
    edit_remote.run(pre + "echo '" + dest_internal_ip + " " + all_domains + "' >> /etc/hosts " + pre)
