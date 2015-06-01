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
Add a newly created ebs volume to a machine

usage add_ebsvol_to_instance.py iid [mount_conf='{"Mount": "/opt",   "Size" : 10, "Attach" : "/dev/sdb",
"Fdisk" : "/dev/xvdb"  }'] [security_config] [--verbose] [--not-strict]

iid: iid of machine to add to
mount_conf : the standard JSON format we use to mount disks on Centos6 correctly, see the description of the
*.aws.json files in the readme
security_config, will be read from $AWSSECCONF if not passed here
--help: print this help and exit

"""

import sys
import os
import json

def help():
    print __doc__


if len(sys.argv) < 2:
    help()
    raise ValueError("You must send enough parameters!")

if "--help" in sys.argv or "-h" in sys.argv:
    help()
    sys.exit(0)

verbose = False
if "--verbose" in sys.argv or "--debug" in sys.argv:
    sys.argv = [s for s in sys.argv if s not in ["--verbose", "--debug"]]
    verbose = True

strict=True
if "--not-strict" in sys.argv:
    sys.argv = [s for s in sys.argv if s not in ["--not-strict"]]
    strict = False

iid = sys.argv[1]
mount_conf = {"Mount": "/opt", "Size": 10, "Attach": "/dev/sdb", "Fdisk": "/dev/xvdb"}
security_config = None

if len(sys.argv) > 2:
    mount_conf = json.loads(sys.argv[2])

if len(sys.argv) > 3:
    security_config = os.path.expanduser(sys.argv[3])
else:
    if "AWSSECCONF" not in os.environ:
        print __doc__
        raise IOError("please specify keyfile or set AWSSECCONF environment variable!")
    security_config = os.path.expanduser(os.environ["AWSSECCONF"])
try:
    jsondat = open(security_config)
    security_config_json = json.loads(jsondat.read())
    jsondat.close()
    ssh_keyfile = security_config_json["AccessKeys"]["SSH"]["KeyFile"]
except KeyError:
    raise KeyError('Your security config file must contain ["AccessKeys"]["SSH"]["KeyFile"] ' + security_config)

instancegroups = {}

installfrom = os.path.realpath(os.path.dirname(__file__))
liblocation = os.path.realpath(installfrom + '/../lib')
sys.path.append(liblocation)

import libAws as lA
import libDeploy as lD
lD.debug = verbose
lD.strict_host_key_checking = strict

lA.testaws()
lA.lD.testproxy()

lA.addNewEBSVol(iid, mount_conf, ssh_keyfile)
