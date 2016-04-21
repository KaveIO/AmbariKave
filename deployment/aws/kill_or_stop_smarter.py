#!/usr/bin/env python
##############################################################################
#
# Copyright 2016 KPMG N.V. (unless otherwise stated)
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
usage: kill_or_stop_smarter.py [security_config.json] [--verbose] [-i]

Specify a security conf file, from where I will read the subnet and the keypair id, if note I will get it from the
AWSSECCONF environment variable

-i : interactive mode, also list other machines in this subnet/keypair and ask you explicitly if you want to kill them.

Remove all available volumes

If older than one day:
    stop instance

If older than one week:
    kill stopped instances

Remove all available volumes
"""

import sys
import os


installfrom = os.path.realpath(os.path.dirname(__file__))
liblocation = os.path.realpath(installfrom + '/../lib')
sys.path.append(liblocation)

interactive = False
if "-i" in sys.argv:
    sys.argv = [s for s in sys.argv if s not in ["-i"]]
    interactive = True

if "--help" in sys.argv or "-h" in sys.argv:
    print __doc__
    sys.exit(0)

verbose = False
if "--verbose" in sys.argv or "--debug" in sys.argv:
    sys.argv = [s for s in sys.argv if s not in ["--verbose", "--debug"]]
    verbose = True

import kavedeploy as lD

lD.debug = verbose
lD.testproxy()
import kaveaws as lA

keyfile = ""

if len(sys.argv) > 2:
    print __doc__
    raise ValueError("Only one arguement allowed! The keyfile/security config")

if len(sys.argv) == 2:
    keyfile = sys.argv[1]
else:
    if "AWSSECCONF" not in os.environ:
        print __doc__
        raise IOError("please specify keyfile or set AWSSECCONF environment variable!")
    keyfile = os.path.expanduser(os.environ["AWSSECCONF"])

import json

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
    raise ValueError("no such subnet " + sn)

# find all instances in the subgroup/subnet
instances = lA.runawstojson(
    "ec2 describe-instances --filters Name=subnet-id,Values=" + subnet + " --filters Name=key-name,Values=" +
    amazon_keypair_name)
# print instances

i_older_than_one_day = []
i_older_than_one_week = []
i_all = []

exclude_names = [".*_dev_.*"]
# Exclude _dev_box names!
import re
import datetime

for reservation in instances["Reservations"]:
    for instance in reservation["Instances"]:
        skip = False
        # print instance.keys()
        if "Tags" in instance.keys():
            for tag in instance["Tags"]:
                if tag["Key"] == "Name":
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
        # print days # bigger than 0 days, or bigger than 20 hours.
        if instance["State"]["Name"] is "running" and days > 0 or seconds > 72000:
            i_older_than_one_day.append(instance["InstanceId"])
        if instance["State"]["Name"] is not "terminated" and days > 6:
            i_older_than_one_week.append(instance["InstanceId"])

yn_ids = None
if len(i_older_than_one_day) + len(i_older_than_one_week):
    print "Stopping:", i_older_than_one_day
    print "Terminating:", i_older_than_one_week
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
    for iid in i_older_than_one_day:
        try:
            lA.killinstance(iid, "stop")
        except RuntimeError:
            failed.append(iid)
    time.sleep(5)
    for iid in i_older_than_one_week:
        try:
            lA.killinstance(iid)
        except RuntimeError:
            failed.append(iid)
    time.sleep(5)

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
        except RuntimeError:
            failed.append(volID)

if yn_ids in yes:
    print "Stopped:", [s for s in i_older_than_one_day if s not in failed]
    print "Terminated:", [s for s in i_older_than_one_week if s not in failed]

if yn_vls in yes:
    print "Deleted:", [s for s in vol_to_kill if s not in failed]

if len(failed):
    print "Warning: Failed to modify states of:", failed

if not interactive:
    oodfails = len([s for s in i_older_than_one_day if s in failed])
    oowfails = len([s for s in i_older_than_one_week if s in failed])
    vtkfails = len([s for s in vol_to_kill if s in failed])
    # at least one failure, at least one request, and they all failed, this should be a big problem!
    tmoodfails = (oodfails and len(i_older_than_one_day) and oodfails == len(i_older_than_one_day))
    tmoowfails = (oowfails and len(i_older_than_one_week) and oowfails == len(i_older_than_one_week))
    tmvtkfails = (vtkfails and len(vol_to_kill) and vtkfails == len(vol_to_kill))
    if tmoodfails or tmoowfails or tmvtkfails:
        raise RuntimeError(
            "Entire categories failed to change state :( review status on ec2 webpage! Or try again in interactive "
            "mode.")
    sys.exit(0)

iidtoip = {}
nametoip = {}
ips = []

print "Interactive mode, yes no for each remaining machine"
print "Name,      iid,     SecGroup(s),   itype,   publicIP, status"
for reservation in instances["Reservations"]:
    for instance in reservation["Instances"]:
        iid = instance["InstanceId"]
        name = "??"
        if 'Tags' in instance:
            names = [tag["Value"] for tag in instance['Tags'] if tag["Key"] == "Name"]
            if len(names):
                name = names[0]
        ip = "??"
        if "PublicIpAddress" in instance:
            ip = str(instance["PublicIpAddress"])
        if iid in i_all and (
            (iid not in i_older_than_one_day and iid not in i_older_than_one_week) or yn_ids not in yes) and str(
                instance["State"]["Name"]) not in ["Terminated", "terminated"]:
            print str(name), str(instance['InstanceId']), [str(group['GroupName']) for group in
                                                           instance['SecurityGroups']], str(
                instance['InstanceType']), ip, str(instance["State"]["Name"])
            iidtoip[str(instance['InstanceId'])] = ip
            nametoip[str(name)] = ip
            ips.append(ip)

iid = None
while iid is None:
    try:
        iid = raw_input("Choose iid [q or ctrl-C to quit]: ")
    except KeyboardInterrupt:
        print " .. quitting"
        break
    if iid in ['q', 'Q']:
        break
    if iid not in iidtoip:
        print "Error, please try again"
        iid = None
        continue
    yn_i = raw_input("Terminating:, " + iid + ", OK? y/[n]").lower().strip()
    if yn_i in yes:
        lA.killinstance(iid)
    iid = None
    continue
