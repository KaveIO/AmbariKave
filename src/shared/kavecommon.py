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
This file will be copied to the scripts directory of each service we have added

to use in your service, import kavecommon as kc
"""
import os
import shutil
import subprocess as sub
from pwd import getpwnam
from grp import getgrnam

# defaults for the repository
#
# NB: the repository server uses a semi-private password only as a means of avoiding robots and reducing DOS attacks
#  this password is intended to be widely known and is used here as an extension of the URL
#
__repo_url__ = "http://repos:kaverepos@repos.kave.io"
__version__ = "2.2-Beta-Pre"
__main_dir__ = "AmbariKave"
__mirror_list_file__ = "/etc/kave/mirror"


def shell_call_wrapper(cmd):
    proc = sub.Popen(cmd, shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
    stdout, stderr = proc.communicate()
    status = proc.returncode
    return status, stdout, stderr


try:
    # when unit testing, res might not be importable, so replace execute with shell_call_wrapper
    import resource_management as res
except ImportError:
    class Object(object):
        pass

    res = Object()
    res.Execute = shell_call_wrapper

    class Script(object):
        pass

    res.Script = Script


def detect_linux_version():
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
        elif "el6" in output:
            return "Centos6"
        elif "el7" in output:
            return "Centos7"
        return None

    # try commands first...
    for cmd in ["cat /etc/redhat-release", "lsb_release -a", "uname -r"]:
        output = shell_call_wrapper(cmd)[1]
        v = find_return(output)
        if v:
            return v
    raise SystemError("Cannot detect linux version, meaning this is not a compatible version")


def is_true_redhat():
    """
    Return true if /etc/redhat-release begins with Red Hat
    """
    fn = '/etc/redhat-release'
    if os.path.exists(fn):
        with open(fn) as fp:
            rf = fp.read()
            return rf.startswith("Red Hat")
    return False


def repo_url(filename, repo=__repo_url__, arch=None, dir=__main_dir__, ver=__version__):
    """
    Construct the repository address for our code
    """
    if arch is None:
        arch = detect_linux_version()
    if repo[-1] != '/':
        repo = repo + '/'
    return repo + arch.lower() + "/" + dir + "/" + ver + "/" + filename


def mirrors():
    __mirror_list__ = []
    if os.path.exists(__mirror_list_file__):
        f = open(__mirror_list_file__)
        ls = f.readlines()
        f.close()
        for mirror in ls:
            mirror = mirror.strip()
            if not len(mirror):
                continue
            if mirror[-1] != '/':
                mirror = mirror + '/'
            __mirror_list__.append(mirror)
    return __mirror_list__


def trueorfalse(astring):
    """
    Boolean cast from a string, understanding most ways of saying yes
    if I don't understand it, raise a TypeError
    """
    cnv = {'true': True, 'y': True, 'ye': True, 'yes': True, 'positive': True, 'affirmative': True,
           'aye': True, 'certainly': True, 'yep': True, 'indubitably': True, 'ok': True, 'okay': True,
           'o.k.': True, 'yeah': True, 'positively': True, 'sure': True, 'ja': True, 'one': True,
           'agree': True, 'false': False, 'n': False, 'no': False, 'none': False, 'negative': False,
           'nope': False, 'never': False, 'nix': False, 'nay': False, 'nee': False, 'refuse': False,
           'abort': False, 'veto': False, 'negatory': False, 'null': False, 'zero': False, 'stop': False}
    ts = type(astring)
    if ts is bool:
        return astring
    elif ts is str or ts is unicode:
        astring = astring.lower().strip()
        try:
            return cnv[astring]
        except KeyError:
            pass
        if not len(astring):
            return False
    elif astring is None:
        return False
    elif ts is int:
        return bool(astring)
    raise TypeError("Cannot guess boolean value equivalent for " + str(astring))


def copymethods(source, destination):
    """
    Construct the command to run, wget if the file is remote, cp if the file is local
    """
    if source.startswith("ftp:") or source.startswith("http"):
        return "wget '" + source + "' -O " + destination
    if os.path.exists(os.path.expanduser(source)):
        return "cp " + source + " " + destination
    raise IOError("no method to copy from " + source)


def failover_source(sources):
    """
    try a list of locations where a file could be, one after the other
    """
    for source in sources:
        if source is None:
            continue
        if source.startswith("ftp:") or (source.startswith("http") and ":" in source):
            _stat, stdout, _stderr = shell_call_wrapper("curl --retry 5 -i -X HEAD " + source)
            if "200 OK" not in stdout and "302 Found" not in stdout:
                continue
            return source
        elif os.path.exists(os.path.expanduser(source)):
            return source
    raise IOError("no available sources detected from the options " + sources.__str__())


def copy_or_cache(sources, filename, cache_dir=None):
    """
    Try a list of sources, first cache the file before copying locally for install
    """
    if type(sources) is str:
        sources = [sources]
    if cache_dir is not None and os.path.isfile(cache_dir + os.sep + filename):
        shutil.copyfile(cache_dir + os.sep + filename, filename)
    else:
        source = failover_source(sources)
        res.Execute(copymethods(source, filename))
        if cache_dir is not None:
            if not os.path.exists(cache_dir):
                res.Execute("mkdir -p " + cache_dir)
            shutil.copyfile(filename, cache_dir + os.sep + filename)
    return


def copy_cache_or_repo(filename, cache_dir=None, arch=None, dir=__main_dir__, ver=__version__, alternates=None):
    """
    Combines all the little functions above into a simple piece of code to copy stuff of the internet from our repo
    or from the local cache

    filename: the filename to find or use
    cache_dir: a local cache, default None - no cache
    arch: the architecture to use on the repo server, default Centos6, but you can consider noarch also
    dir: the repo master directory name, usually AmbariKave
    ver: the version to look at in the repo, set above
    alternates: other places to look for this file in case the repo is down, these need to be complete URLs to the file
    """
    # default goes last
    sources = []
    for mirror in mirrors():
        sources.append(repo_url(filename, arch=arch, repo=mirror, dir=dir, ver=ver))
    sources.append(repo_url(filename, arch=arch, dir=dir, ver=ver))
    if type(alternates) is list:
        sources = sources + alternates
    if type(alternates) is str:
        sources.append(alternates)
    return copy_or_cache(sources=sources, filename=filename, cache_dir=cache_dir)


def chown_r(adir, user):
    """
    recursive chown wrapper, chown all lower files
    """
    os.chown(adir, getpwnam(user).pw_uid, getgrnam(user).gr_gid)
    for root, dirs, files in os.walk(adir):
        for momo in dirs:
            os.chown(os.path.join(root, momo), getpwnam(user).pw_uid, getgrnam(user).gr_gid)
        for momo in files:
            os.chown(os.path.join(root, momo), getpwnam(user).pw_uid, getgrnam(user).gr_gid)


def chmod_up(lowest, mode, seen=[]):
    """
    chmod wrapper, add certain modes to all directories walking up towards root
    """
    lowest = os.path.realpath(lowest)
    if lowest in seen:
        return
    # prevent infinite recursion!
    seen.append(lowest)
    if lowest == '/':
        return
    elif not os.path.exists(lowest):
        return
    elif not len(lowest):
        return
    res.Execute('chmod ' + mode + ' ' + lowest)
    if lowest.count("/") < 2:
        # prevent infinite recursion!
        return
    if lowest == os.path.realpath(os.sep.join(lowest.split(os.sep)[:-1])):
        # prevent infinite recursion!
        return
    return chmod_up(os.sep.join(lowest.split(os.sep)[:-1]), mode, seen=seen)


def check_port(number):
    """
    Check if a port is in use and return details about what is using the port
    Proto Recv-Q Send-Q, Local Address, Foreign Address, State, User, Inode, PID/Program name
    """
    _status, stdout, _stderr = shell_call_wrapper("netstat -lpe | grep ':" + str(number) + "'")
    stdout = stdout.strip().split()
    if len(stdout) < 4:
        return None
    if stdout[3].endswith(':' + str(number)):
        return stdout
    return None
    # old code with psutil
    import psutil
    for portstat in psutil.net_connections():
        # Return system-wide connections as a list of
        # (fd, family, type, laddr, raddr, status, pid) namedtuples.
        if int(number) == int(portstat[3][-1]):
            return portstat
    return None


def ps(number):
    """
    return ps details for this process
    UID        PID  PPID  C STIME TTY      STAT   TIME CMD
    """
    _status, stdout, _stderr = shell_call_wrapper("ps -f " + str(number) + " | grep " + str(number))
    stdout = stdout.strip().split()
    if len(stdout) < 4:
        return None
    if stdout[1] == str(number):
        return stdout[0:8] + [stdout[8:]]
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


def install_epel(clean=True):
    if detect_linux_version() in ["Centos6"]:
        res.Execute('yum -y install epel-release')
    else:
        status, stdout, _stderr = shell_call_wrapper('yum info epel-release')
        if status or 'installed' not in stdout:
            res.Execute('yum -y install wget')
            res.Execute('wget https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm')
            res.Execute('yum -y install epel-release-latest-7.noarch.rpm')
    if clean:
        res.Execute('yum clean all')


class ApacheScript(res.Script):
    """
    Common script class for apache web pages
    requires: a params file called params with:
        www_folder
        PORT
    a templates directory with a copy of 000_default.conf
    """

    def install(self, env):
        print "installing apache..."
        self.install_packages(env)
        import params

        env.set_params(params)
        res.Execute("mkdir -p " + params.www_folder)
        chown_r(params.www_folder, "apache")
        # self.configure(env)
        # self.start(env)

    def configure(self, env):
        import params

        env.set_params(params)
        res.Execute('chkconfig httpd on')
        res.File('/etc/httpd/conf.d/000_default.conf',
                 content=res.InlineTemplate(params.template_000_default),
                 mode=0644
                 )
        chown_r('/etc/httpd/conf.d/', "apache")
        chown_r(params.www_folder, "apache")
        if not os.path.isfile('/etc/httpd/conf/httpd.conf'):
            raise RuntimeError("Service not installed correctly")
        os.system("grep -v '^Listen' /etc/httpd/conf/httpd.conf > tmp.cnf")
        f = open("tmp.cnf")
        r = f.read()
        f.close()
        if len(r) < 13 or "ServerRoot" not in r:
            raise IOError("Temporary httpd.conf file corrupted!")
        res.Execute("cp tmp.cnf /etc/httpd/conf/httpd.conf")
        chown_r('/etc/httpd/conf/', "apache")

    def start(self, env):
        print "start apache"
        self.configure(env)

        import time
        if detect_linux_version() in ["Centos7"]:
            # wait 3 seconds before calling start
            time.sleep(3)
            try:
                res.Execute("service httpd start")
            except:
                res.Execute("apachectl graceful")

        time.sleep(3)
        res.Execute("apachectl graceful")
        time.sleep(3)

    def stop(self, env):
        print "stop apache.."
        res.Execute('service httpd stop')

    def status(self, env):
        print "checking status..."
        res.Execute('service httpd status')
