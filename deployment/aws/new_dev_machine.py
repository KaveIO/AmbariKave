#!/usr/bin/env python
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
New dev machine will create a new machine on amazon for a particular user
It will currently make a c4.2xlarge machine

usage: new_dev_machine.py username [--verbose]

optional:
    --verbose : print all remotely running commands

Will read $AWSSECCONF for the security config file
"""

# up new instance

import os
import sys
import time
import json
import getpass


installfrom = os.path.realpath(os.path.dirname(__file__))
liblocation = os.path.realpath(installfrom + '/../lib')
sys.path.append(liblocation)

import kavedeploy as lD

lD.debug = False
lD.strict_host_key_checking = False
import kaveaws as lA


def help():
    print __doc__
    # sys.exit(code)


def parse_opts():
    if "-h" in sys.argv or "--help" in sys.argv:
        help()
        sys.exit(0)
    if "--verbose" in sys.argv:
        lD.debug = True
        sys.argv = [s for s in sys.argv if s != "--verbose"]
    if len(sys.argv) > 2:
        help()
        raise AttributeError("You supplied too many arguments")
    if len(sys.argv) < 2:
        help()
        raise AttributeError("You supplied too few arguments")
    username = sys.argv[1]
    password = getpass.getpass("Password for user " + username + ": ")
    return username, password


base = os.path.dirname(__file__)

if "AWSSECCONF" not in os.environ:
    help()
    raise IOError("please set AWSSECCONF environment variable!")

secf = os.path.expanduser(os.environ["AWSSECCONF"])

username, password = parse_opts()
jsondat = open(secf)
security_config = json.loads(jsondat.read())
jsondat.close()
lA.checksecjson(security_config, requirekeys=["AWS"])

security_group = security_config["SecurityGroup"]
keypair = security_config["AccessKeys"]["AWS"]["KeyName"]
keyloc = security_config["AccessKeys"]["AWS"]["KeyFile"]
subnet = None

if "Subnet" in security_config:
    subnet = security_config["Subnet"]

lA.testaws()

instancetype = lA.chooseinstancetype("c4.2xlarge")

##################################################
# Create machine
##################################################

print "upping new", instancetype
if lD.detect_proxy() and lD.proxy_blocks_22:
    raise SystemError(
        "This proxy blocks port 22, that means you can't ssh to your machines to do the initial configuration. To "
        "skip this check set kavedeploy.proxy_blocks_22 to false and kavedeploy.proxy_port=22")
lD.testproxy()

upped = lA.up_default(instancetype, security_group, keypair, subnet=subnet)
print "submitted"
iid = lA.iid_from_up_json(upped)[0]
import time

time.sleep(5)
lA.name_resource(iid, username + "_dev_box")
ip = lA.pub_ip(iid)
acount = 0
while (ip is None and acount < 20):
    print "waiting for IP"
    lD.mysleep(1)
    ip = lA.pub_ip(iid)
    acount = acount + 1

remoteuser = lA.default_usernamedict[lA.default_os]
remote = lD.remoteHost(remoteuser, ip, keyloc)
print "waiting until contactable"
lD.wait_until_up(remote, 20)
remote = lD.remote_cp_authkeys(remote, 'root')
if "Tags" in security_config:
    resources = lA.find_all_child_resources(iid)
    lA.tag_resources(resources, security_config["Tags"])
remote.register()

##################################################
# Renaming, configuring firewall and adding more disk space
##################################################
print "Renaming, configuring firewall and adding more disk space"
lD.rename_remote_host(remote, username + "_dev_box", 'kave.io')
remote.run("mkdir -p /etc/kave/")
remote.run("/bin/echo http://repos:kaverepos@repos.dna.kpmglab.com/ >> /etc/kave/mirror")
lD.add_as_host(edit_remote=remote, add_remote=remote, dest_internal_ip=lA.priv_ip(iid))
lD.configure_keyless(remote, remote, dest_internal_ip=lA.priv_ip(iid), preservehostname=True)
# This is not needed for Centos7
tos = remote.detect_linux_version()
lD.disable_security(remote)

lD.confallssh(remote, restart=False)
lD.confremotessh(remote, restart=False)
lD.confsshpermissions(remote)
vols = []
vols.append(lA.add_new_ebs_vol(iid, {"Mount": "/opt", "Size": 10, "Attach": "/dev/sdb"}, keyloc))
vols.append(lA.add_new_ebs_vol(iid, {"Mount": "/var/log", "Size": 2, "Attach": "/dev/sdc"}, keyloc))
vols.append(lA.add_new_ebs_vol(iid, {"Mount": "/home", "Size": 100, "Attach": "/dev/sdd"}, keyloc))

remote.describe()
if "Tags" in security_config:
    lA.tag_resources(vols, security_config["Tags"])
print "OK, iid " + iid + " now lives at IP " + ip

##################################################
# Installing vnc
##################################################
# print "installing vnc and gnome desktop"
# remote.run('yum -y install epel-release')
# remote.run('yum clean all')
# remote.run("yum -y install vim emacs wget curl zip unzip tar gzip rsync git")
# if tos in ["Centos6"]:
#    remote.run('yum -y groupinstall "Desktop" "Desktop Platform" '
#               '"X Window System" "Fonts" --exclude=NetworkManager\\*')
# else:
#    remote.run('yum -y install pixman pixman-devel libXfont')
#    remote.run('yum -y groupinstall "Gnome Desktop" "Fonts" ')
#
# remote.run('yum -y tigervnc-server')
# remote.run('yum -y install xpdf firefox')

################################################
# Add user and add to sudoers
################################################

remote.run('useradd ' + username)
remote.run('bash -c \'echo "' + username + ' ALL=(ALL:ALL) ALL" | (EDITOR="tee -a" visudo)\'')

################################################
# Try configuring password
################################################
import tempfile
tempdir = ''
try:
    tempdir = tempfile.mkdtemp()
    tempdir = tempdir + '/'
    fname = username + ip
    with open(tempdir + fname, 'w') as fp:
        fp.write(password + '\n')
        fp.write(password + '\n')
    remote.cp(tempdir + fname, fname)
    remote.run('cat ' + fname + ' | passwd ' + username)
    remote.run('rm -f ' + fname)
except Exception as e:
    if os.path.exists(tempdir):
        os.system('rm -rf ' + tempdir)
    raise e

################################################
# Add KaveToolbox
################################################
lD.deploy_our_soft(remote, pack="kavetoolbox", version='3.2-Beta', options='--workstation')


print "OK, iid " + iid + " now lives at IP " + ip
remote.describe()
