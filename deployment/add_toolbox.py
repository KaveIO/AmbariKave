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
Add the KaveToolbox to a remote machine (or amazon instance)

usage add_toolbox_to_centos_instance.py host security_config.json [--ip/--iid] [--node/--workstation] [--verbose]

host: the ip or instance id of the machine to configure
security_config.json, standard security file which at least has the git and SSH access keys to use

[--ip/--iid] defines if the host should be seen as an ip or as an amazon instance id
[--node/--workstation], default --node, whether to install the toolbox as a node or as a complete workstation
[--verbose] : print all remotely running commands
[--not-strict] : turn off strict host-key checking
"""

import os
import sys
import time
import json


def help():
    print __doc__
    #sys.exit(code)


installfrom = os.path.realpath(os.path.dirname(__file__))
liblocation = os.path.realpath(installfrom + '/lib')
sys.path.append(liblocation)

import kavedeploy as lD

lD.debug = False


def parseOpts():
    if "-h" in sys.argv or "--help" in sys.argv:
        help()
        sys.exit(0)
    if "--verbose" in sys.argv:
        lD.debug = True
        sys.argv = [s for s in sys.argv if s != "--verbose"]
    if "--not-strict" in sys.argv:
        sys.argv = [s for s in sys.argv if s not in ["--not-strict"]]
        lD.strict_host_key_checking = False
    node = ("--node" in sys.argv)
    workstation = ("--workstation" in sys.argv)
    ip = ("--ip" in sys.argv)
    iid = ("--iid" in sys.argv)
    if len([i for i in sys.argv if not i.startswith("--")]) < 2:
        help()
        raise AttributeError("You must supply a host and a security config json file")
    if workstation and node:
        help()
        raise AttributeError("you can't set both workstation and node")
    if not workstation:
        node = True
    if ip and iid:
        help()
        raise AttributeError("you can't set both iid and ip")
    if not ip and not iid:
        help()
        raise AttributeError("you must specify either --iid or --ip")
    if workstation:
        dest_type = "workstation"
    else:
        dest_type = "node"
    otherargs = [i for i in sys.argv if not i.startswith("--")]
    if ip:
        ip = otherargs[1]
        iid = None
    else:
        iid = otherargs[1]
        ip = None
    return (ip, iid, otherargs[2], dest_type)


if __name__ == "__main__":
    ip, iid, security_conf, dest_type = parseOpts()
    #only needed in main function
    installfrom = os.path.realpath(os.sep.join(__file__.split(os.sep)[:-1]))
    liblocation = os.path.realpath(installfrom)
    jsondat = open(os.path.expanduser(security_conf))
    security_config = json.loads(jsondat.read())
    jsondat.close()
    sys.path.append(liblocation)
    import kavedeploy as lD
    import kaveaws as lA

    lA.checksecjson(security_config, requirefield=[], requirekeys=["SSH"])
    if ip is None:
        lA.testaws()
        ip = lA.pubIP(iid)
    git = False
    gitenv = None
    if lD.detect_proxy():
        print "Did you already configure this machine to access port " + str(
            lD.proxy_port) + "? If not you'll need to turn your proxy off."
    lD.testproxy()
    remote = lD.remoteHost('root', ip, security_config["AccessKeys"]["SSH"]["KeyFile"])
    if "GIT" in security_config["AccessKeys"]:
        git = True
        gitenv = security_config["AccessKeys"]["GIT"]
    lD.deployOurSoft(remote, pack="kavetoolbox", git=git, gitenv=gitenv)
    #if dest_type == "workstation":
    #    lD.confremotessh(remote)
