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
New dev image will first create a new centos7 machine and install the head of ambari onto it.
It will then stop that instance and create an image from that instance, returning the ami registered id

usage: new_dev_image.py [iid] [--verbose] [--skip-ambari] [--skip-blueprint]

optional:
    iid: an instance that already exists with these keys
    --verbose : print all remotely running commands
    --skip-ambari : skip installing of ambari itself, move straight to blueprint deploy
    --skip-blueprint : skip blueprint deploy, move straight to image creation

Will read $AWSSECCONF for the security config file
"""

# up new instance

import os
import sys
import time
import json


installfrom = os.path.realpath(os.path.dirname(__file__))
liblocation = os.path.realpath(installfrom + '/../lib')
sys.path.append(liblocation)

import kavedeploy as lD

lD.debug = False
lD.strict_host_key_checking = False
import kaveaws as lA

skip_ambari = False
skip_blueprint = False
version = "latest"


def help():
    print __doc__
    # sys.exit(code)


def parse_opts():
    global skip_ambari
    global skip_blueprint
    global version
    if "-h" in sys.argv or "--help" in sys.argv:
        help()
        sys.exit(0)
    if "--skip-ambari" in sys.argv:
        skip_ambari = True
        sys.argv = [s for s in sys.argv if s != "--skip-ambari"]
    if "--skip-blueprint" in sys.argv:
        skip_blueprint = True
        sys.argv = [s for s in sys.argv if s != "--skip-blueprint"]
    if "--verbose" in sys.argv:
        lD.debug = True
        sys.argv = [s for s in sys.argv if s != "--verbose"]
    if "--this-branch" in sys.argv:
        version = lD.run_quiet(
            "bash -c \"cd " + os.path.dirname(__file__) + "; git branch | sed -n '/\* /s///p'\"")
        stdout = lD.run_quiet("bash -c 'cd " + os.path.dirname(__file__) + "; git branch -r;'")
        if ("origin/" + version not in [s.strip() for s in stdout.split() if len(s.strip())]):
            raise AttributeError("There is no remote branch called " + version
                                 + " push your branch back to the origin to deploy")
        sys.argv = [s for s in sys.argv if s != "--this-branch"]
    if len(sys.argv) > 2:
        help()
        raise AttributeError("You supplied too many arguments")
    iid = None
    if len(sys.argv) > 1:
        iid = sys.argv[1]
    return iid


base = os.path.dirname(__file__)
if (not os.path.exists(base + "/../blueprints/default.blueprint.json")) or (
        not os.path.exists(base + "/../blueprints/default.cluster.json")):
    raise IOError("What happened to default.blueprint.json and default.cluster.json? I can't find them :S")

if "AWSSECCONF" not in os.environ:
    help()
    raise IOError("please set AWSSECCONF environment variable!")

secf = os.path.expanduser(os.environ["AWSSECCONF"])

iid = parse_opts()
jsondat = open(secf)
security_config = json.loads(jsondat.read())
jsondat.close()
lA.checksecjson(security_config, requirekeys=["AWS"])

security_group = security_config["SecurityGroup"]
keypair = security_config["AccessKeys"]["AWS"]["KeyName"]
keyloc = security_config["AccessKeys"]["AWS"]["KeyFile"]
git = False
gitenv = None
if "GIT" in security_config["AccessKeys"]:
    git = True
    gitenv = security_config["AccessKeys"]["GIT"]
subnet = None

if "Subnet" in security_config:
    subnet = security_config["Subnet"]

lA.testaws()

instancetype = lA.chooseinstancetype("m4.large")

if iid is None:
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
    lA.name_resource(iid, "new-dev-image")
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
    print "Renaming, configuring firewall and adding more disk space"
    lD.rename_remote_host(remote, "ambari", 'kave.io')
    remote.run("mkdir -p /etc/kave/")
    remote.run("/bin/echo http://repos:kaverepos@repos.dna.kpmglab.com/ >> /etc/kave/mirror")
    lD.add_as_host(edit_remote=remote, add_remote=remote, dest_internal_ip=lA.priv_ip(iid))
    lD.configure_keyless(remote, remote, dest_internal_ip=lA.priv_ip(iid), preservehostname=True)
    # nope! Don't want 443 as ssh by default any longer!
    # lD.confremotessh(remote)
    # This is not needed for Centos7
    lD.disable_security(remote)
    lD.confallssh(remote)
    vols = []
    vols.append(lA.add_new_ebs_vol(iid, {"Mount": "/opt", "Size": 10, "Attach": "/dev/sdb"}, keyloc))
    vols.append(lA.add_new_ebs_vol(iid, {"Mount": "/var/log", "Size": 2, "Attach": "/dev/sdc"}, keyloc))
    vols.append(lA.add_new_ebs_vol(iid, {"Mount": "/usr/hdp", "Size": 4, "Attach": "/dev/sdd"}, keyloc))
    tos = remote.detect_linux_version()
    if tos in ["Centos7"]:
        vols.append(lA.add_new_ebs_vol(
            iid, {"Mount": "/var/lib/ambari-agent", "Size": 1, "Attach": "/dev/sde"}, keyloc))
        vols.append(lA.add_new_ebs_vol(
            iid, {"Mount": "/var/lib/ambari-server", "Size": 2, "Attach": "/dev/sdf"}, keyloc))
    elif tos in ["Centos6"]:
        vols.append(lA.add_new_ebs_vol(iid, {"Mount": "/var/lib", "Size": 4, "Attach": "/dev/sde"}, keyloc))
    remote.describe()
    if "Tags" in security_config:
        lA.tag_resources(vols, security_config["Tags"])
    print "OK, iid " + iid + " now lives at IP " + ip

ip = ""
remote = ""
if (not skip_ambari) or (not skip_blueprint):
    ip = lA.pub_ip(iid)
    remote = lD.remoteHost('root', ip, keyloc)
    lD.configure_keyless(remote, remote, lA.priv_ip(iid), preservehostname=True)
#
#
# INSTALL AMBARI HEAD and Deploy a very simple default blueprint!
#
#
if not skip_ambari:
    print "Installing ambari " + version + " from git"
    lD.deploy_our_soft(remote, version=version, git=git, gitenv=gitenv)
    print "Awaiting ambari installation ..."
    lD.wait_for_ambari(remote, check_inst=['inst.stderr', 'inst.stdout'])

if not skip_blueprint:
    print "Deploying default blueprint"
    stdout = lD.run_quiet(
        base + "/../deploy_from_blueprint.py --not-strict " + base + "/../blueprints/default.blueprint.json " + base
        + "/../blueprints/default.cluster.json " + remote.host + " " + secf)
    print stdout
    print "Awaiting blueprint completion"
    lD.waitforrequest(remote, 'default', 1)

#
#
# Stop the instance and create an image from it!
#
#
print "Creating image from this installation"
instance = lA.desc_instance(iid)["Reservations"][0]["Instances"][0]
# print instance
if instance["State"]["Name"] is "running":
    lA.killinstance(iid, "stop")
    lA.waitforstate(iid, "stopped")
# wait until stopped
ami = lA.createimage(iid, "AmbDev-" + keypair + "-" + time.strftime("%Y%m%d-%H"),
                     "Ambari dev image with keys for " + keypair + " keypair")
time.sleep(5)
lA.name_resource(ami, keypair)
print ami, "created and registered, might take a few minutes to be available,",
print " don't forget to set your environment variable export AMIAMBDEV=" + ami
