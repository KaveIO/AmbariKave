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
usage: kill_recent_tests.py [hours=6] [security_config.json] [--verbose]

Specify a security conf file, from where I will read the subnet and the keypair id,
if none I will get it from the AWSSECCONF environment variable

Remove all available volumes

If younger than X hours and "Test" in the name:
    terminate instance

If younger than X hours, older than two hours, and "new-dev-image" in the name:
    terminate instance

If stopped and "Test" in the name and older than 22 hours:
    terminate instance

Remove all available volumes
"""

import sys
import os
import json
import re
import datetime


installfrom = os.path.realpath(os.path.dirname(__file__))
liblocation = os.path.realpath(installfrom + '/../deployment/lib')
sys.path.append(liblocation)

import kavedeploy as lD
import kaveaws as lA

if "--help" in sys.argv or "-h" in sys.argv:
    print __doc__
    sys.exit(0)

verbose = False
if "--verbose" in sys.argv or "--debug" in sys.argv:
    sys.argv = [s for s in sys.argv if s not in ["--verbose", "--debug"]]
    verbose = True

lD.debug = verbose
lD.testproxy()

keyfile = ""

hours = 6

if len(sys.argv) == 2:
    try:
        hours = int(sys.argv[1])
    except ValueError:
        keyfile = sys.argv[1]
elif len(sys.argv) == 3:
    try:
        hours = int(sys.argv[2])
    except ValueError:
        keyfile = sys.argv[2]


if hours > 23:
    raise ValueError("I can only kill less than 24 hour old stuff, otherwise, do it yourself manually")

if len(sys.argv) > 3:
    print __doc__
    raise ValueError("Only two arguements allowed! The keyfile/security config and the hours")

if not len(keyfile):
    if "AWSSECCONF" not in os.environ:
        print __doc__
        raise IOError("please specify keyfile or set AWSSECCONF environment variable!")
    keyfile = os.path.expanduser(os.environ["AWSSECCONF"])


jsondat = open(keyfile)
security_config = json.loads(jsondat.read())
jsondat.close()
lA.checksecjson(security_config)
amazon_keypair_name = security_config["AccessKeys"]["AWS"]["KeyName"]
subnet = security_config["Subnet"]

existing_sn = lA.runawstojson("ec2 describe-subnets")  # "GroupId": "sg-c7c322b1"

found = False
for existing in existing_sn["Subnets"]:
    if existing["SubnetId"] == subnet:
        found = True
        break
if not found:
    raise ValueError("no such subnet " + subnet)

#
# Find and kill all instances
#

# find all instances in the subgroup/subnet
instances = lA.runawstojson(
    "ec2 describe-instances --filters Name=subnet-id,Values=" + subnet + " --filters Name=key-name,Values=" +
    amazon_keypair_name)
# print instances

i_younger_than_x_hours = []
i_stopped = []
i_all = []

exclude_names = [".*_dev_.*"]
require_names = ["test.*", "Test.*"]
dev_names = ["new-dev-image"]

# Exclude _dev_box names!

for reservation in instances["Reservations"]:
    for instance in reservation["Instances"]:
        skip = True
        dev = False
        # print instance.keys()
        if "Tags" in instance.keys():
            for tag in instance["Tags"]:
                if tag["Key"] == "Name":
                    for req in require_names:
                        if re.match(req, tag["Value"]) is None:
                            continue
                        else:
                            skip = False
                            break
                    for req in dev_names:
                        if re.match(req, tag["Value"]) is None:
                            continue
                        else:
                            skip = False
                            dev = True
                            break
                    for ex in exclude_names:
                        if re.match(ex, tag["Value"]) is not None:
                            skip = True
                            break
                    if skip:
                        break
        if skip:
            continue
        i_all.append(instance["InstanceId"])
        # print instance["LaunchTime"]
        lt = datetime.datetime.strptime(instance["LaunchTime"], "%Y-%m-%dT%H:%M:%S.%fZ")
        # print lt
        days = (datetime.datetime.utcnow() - lt).days
        seconds = (datetime.datetime.utcnow() - lt).seconds
        # print days, seconds, instance["State"]["Name"] # bigger than 0 days, or bigger than 20 hours.
        # print instance["State"]["Name"]=="running", days==0, instance["State"]["Name"]=="stopped"
        if dev and (seconds > (2 * 3600) or days > 0) and days < 5:
            i_younger_than_x_hours.append(instance["InstanceId"])
        if (not dev) and instance["State"]["Name"] == "running" and days == 0 and seconds < (hours * 3600):
            i_younger_than_x_hours.append(instance["InstanceId"])
        if (not dev) and instance["State"]["Name"] == "stopped" and days == 0 and seconds < (hours * 3600):
            i_younger_than_x_hours.append(instance["InstanceId"])
        if (not dev) and instance["State"]["Name"] == "stopped" and (days > 1 or seconds > 79200):
            i_stopped.append(instance["InstanceId"])

yn_ids = None
if len(i_younger_than_x_hours) + len(i_stopped):
    print "Terminating:", i_younger_than_x_hours + i_stopped
    yn_ids = raw_input("Continue? y/[n]").lower().strip()

yes = set(['yes', 'y', 'ye'])
failed = []

if yn_ids in yes:
    print "OK, you have 5 seconds to change your mind",
    sys.__stdout__.flush()
    import time

    for i in range(5):
        time.sleep(1)
        print ".",
        sys.__stdout__.flush()
    print " expired"
    for iid in i_younger_than_x_hours + i_stopped:
        try:
            lA.killinstance(iid)
        except lD.ShellExecuteError:
            failed.append(iid)
    time.sleep(5)

#
# Find and kill all test VPCs created at this moment by this user/keypair
#
stacks_to_delete = []
formations = lA.runawstojson("cloudformation describe-stacks")["Stacks"]
for stack in formations:
    skip = True
    for req in require_names:
        if re.match(req, stack["StackName"]) is None:
            continue
        else:
            skip = False
            break
    for ex in exclude_names:
        if re.match(ex, stack["StackName"]) is not None:
            skip = True
            break
    if amazon_keypair_name not in stack["StackName"] and amazon_keypair_name.replace('_', '') not in stack["StackName"]:
        skip = True
    if stack["StackStatus"] in ["DELETE_IN_PROGRESS"]:
        skip = True
    if skip:
        continue
    stacks_to_delete.append(stack["StackName"])

yn_stk = None
if len(stacks_to_delete):
    print "Deleting:", stacks_to_delete
    yn_stk = raw_input("Continue? y/[n]").lower().strip()

if yn_stk in yes:
    print "OK, you have 5 seconds to change your mind",
    sys.__stdout__.flush()
    import time

    for i in range(5):
        time.sleep(1)
        print ".",
        sys.__stdout__.flush()
    print " expired"
    for stack in stacks_to_delete:
        try:
            lA.runawstojson("cloudformation delete-stack --stack-name " + stack)
        except lD.ShellExecuteError:
            failed.append(stack)
    time.sleep(5)


#
# Find and kill all volumes
#

volumes = lA.runawstojson("ec2 describe-volumes --filters Name=status,Values=available ")

vol_to_kill = [vol["VolumeId"] for vol in volumes['Volumes']]

yn_vls = None
if len(vol_to_kill):
    print "Deleting:", vol_to_kill
    yn_vls = raw_input("Continue? y/[n]").lower().strip()

if yn_vls in yes:
    print "OK, you have 5 seconds to change your mind",
    sys.__stdout__.flush()
    import time

    for i in range(5):
        time.sleep(1)
        print ".",
        sys.__stdout__.flush()
    print " expired"
    for volID in vol_to_kill:
        try:
            lA.killvolume(volID)
        except lD.ShellExecuteError:
            failed.append(volID)

if yn_ids in yes:
    print "Terminated:", [s for s in i_younger_than_x_hours + i_stopped if s not in failed]

if yn_stk in yes:
    print "Deleted:", [s for s in stacks_to_delete if s not in failed]

if yn_vls in yes:
    print "Deleted:", [s for s in vol_to_kill if s not in failed]

if len(failed):
    print "Warning: Failed to modify states of:", failed

yxhfails = len([s for s in i_younger_than_x_hours if s in failed])
sfails = len([s for s in i_stopped if s in failed])
vtkfails = len([s for s in vol_to_kill if s in failed])
stkfails = len([s for s in stacks_to_delete if s in failed])
# at least one failure, at least one request, and they all failed, this should be a big problem!
tmyxhfails = (yxhfails and len(i_younger_than_x_hours) and oodfails == len(i_younger_than_x_hours))
tmsfails = (sfails and len(i_stopped) and oowfails == len(i_stopped))
tmvtkfails = (vtkfails and len(vol_to_kill) and vtkfails == len(vol_to_kill))
tmstkfails = (stkfails and len(stacks_to_delete) and stkfails == len(stacks_to_delete))
if tmyxhfails or tmsfails or tmvtkfails or tmstkfails:
    raise RuntimeError("Entire categories failed to change state :( review status on ec2 webpage!")
