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
Very simple script, gives you back a ssh session on the destination machine.
All running machines are listed and you can choose

Only arguement is the amazon/access keyfile or security config file,
if none is given, reads the value of $AWSSECCONF
"""
import sys
import os

installfrom = os.path.realpath(os.path.dirname(__file__))
liblocation = os.path.realpath(installfrom + '/../lib')
sys.path.append(liblocation)
# print liblocation
if "--help" in sys.argv or "-h" in sys.argv:
    print __doc__
    sys.exit(0)

verbose = False
if "--verbose" in sys.argv or "--debug" in sys.argv:
    sys.argv = [s for s in sys.argv if s not in ["--verbose", "--debug"]]
    verbose = True

keyfile = ""

if len(sys.argv) > 2:
    print __doc__
    raise ValueError("Only one arguement allowed! The keyfile")

if len(sys.argv) == 2:
    keyfile = sys.argv[1]
else:
    if "AWSSECCONF" not in os.environ:
        print __doc__
        raise IOError("please specify keyfile or set AWSSECCONF environment variable!")
    keyfile = os.path.expanduser(os.environ["AWSSECCONF"])

import kavedeploy as lD

lD.debug = verbose
lD.testproxy()
import kaveaws as lA

import json

try:
    jsondat = open(keyfile)
    security_config = json.loads(jsondat.read())
    jsondat.close()
    lA.checksecjson(security_config, requirekeys=["AWS"])
    keyfile = security_config["AccessKeys"]["AWS"]["KeyFile"]
except:
    pass

if not os.path.exists(os.path.expanduser(keyfile)):
    raise IOError("That is not a valid keyfile!", keyfile)
if "------" not in lD.run_quiet("ls -l " + keyfile):
    raise IOError("Your private keyfile " + keyfile + " needs to have X00 permissions (400 or 600).")

print "Choose instance ID from:"
iidtoip = {}
nametoip = {}
ips = []

print "Name,      iid,     security_group(s),   instancetype,   publicIP, status"
json = lA.desc_instance()
for reservation in json["Reservations"]:
    for instance in reservation["Instances"]:
        # print instance
        if "PublicIpAddress" not in instance or not len(instance["PublicIpAddress"]):
            continue
        else:
            name = "??"
            if 'Tags' in instance:
                names = [tag["Value"] for tag in instance['Tags'] if tag["Key"] == "Name"]
                if len(names):
                    name = names[0]
            print str(name), str(instance['InstanceId']), [str(group['GroupName']) for group in
                                                           instance['SecurityGroups']], str(
                instance['InstanceType']), str(instance["PublicIpAddress"]), str(instance["State"]["Name"])
            iidtoip[str(instance['InstanceId'])] = str(instance["PublicIpAddress"])
            nametoip[str(name)] = str(instance["PublicIpAddress"])
            ips.append(str(instance["PublicIpAddress"]))

ip = None
while ip is None:
    ip = raw_input("Choose iid or name or ip: ")
    if ip in ips:
        break  # it was an ip
    if ip in iidtoip:
        ip = iidtoip[ip]
        break  # it was an iid
    if ip in nametoip:
        ip = nametoip[ip]
        break  # it was a name
    print "Error, please try again"
    ip = None

os.system("ssh " + ' '.join(lD.proxopts()) + " -i " + keyfile + " root@" + ip)
