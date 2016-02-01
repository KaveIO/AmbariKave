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
python functions for interacting with aws
"""
#
# Functions specific to AWS
#
import kavedeploy as lD
import commands
import subprocess as sub
import json
import os
import sys
import time
import re

import threading
import thread
import Queue


def testaws():
    try:
        import awscli.clidriver
    except:
        raise SystemError("You have not yet installed awscli, look again at the wiki!")
    return True


def runawstojson(cmd):
    prox = lD.detect_proxy() and no_ssl_over_proxy
    if prox:
        cmd = "--no-verify-ssl " + cmd
    output = lD.runQuiet("aws " + cmd)
    if len(output.strip()):
        return json.loads(output.strip())
    else:
        return {}


def detectRegion():
    """
    return aws cli region setting, needed to choose instance to create tokyo images, should extend it to other
    regions...
    """
    return lD.runQuiet("aws configure get region")

__region_ami_links__ = {"Centos6": {"default": "ami-42718735",  # only paravirtual, 6.5 release media
                                    "eu-west": "ami-30ff5c47",  # good, centos 6 "with updates"
                                    "ap-northeast": "ami-25436924",
                                    "ap-southeast": "aami-0aaf8858"
                                    },
                        "Centos7": {"default": "ami-e4ff5c93",
                                    "eu-west": "ami-e4ff5c93",
                                    "ap-northeast": "ami-89634988",
                                    "ap-southeast": "ami-aea582fc"
                                    },
                        "Ubuntu14": {"default": "ami-5da23a2a",
                                     "eu-west": "ami-47a23a30",
                                     "ap-northeast": "ami-936d9d93",
                                     "ap-southeast": "ami-96f1c1c4"
                                     }
                        }


def chooseamiid(os, region):
    if os not in __region_ami_links__:
        raise ValueError("OS " + os + " not known for linking to amiid")
    try:
        return __region_ami_links__[os][str(region)]
    except KeyError:
        pass
    try:
        return __region_ami_links__[os]['-'.join(str(region).split('-')[:-1])]
    except KeyError:
        pass
    try:
        return __region_ami_links__[os]['default']
    except KeyError:
        pass
    raise ValueError("os/region combination could not be made " + os + str(region))
    return ""


def upCentos6(type, secGroup, keys, count=1, subnet=None, ambaridev=False):
    region = "default"
    amiid = ""
    if subnet is not None:
        region = detectRegion()
    if ambaridev:
        import os
        if "AMIAMBDEV" in os.environ:
            amiid = os.environ["AMIAMBDEV"]
        else:
            raise ValueError(
                "To use the dev option, you must have set AMIAMBDEV environment variable to the ami of a centos6 "
                "image with ambari pre-installed with your keys and in your region. See the script that generates "
                "the dev image for that.")
    else:
        amiid = chooseamiid("Centos6", region)
    return upamiid(amiid, type=type, secGroup=secGroup, keys=keys, count=count, subnet=subnet)


def upOS(os, type, secGroup, keys, count=1, subnet=None):
    region = "default"
    amiid = ""
    if subnet is not None:
        region = detectRegion()
    amiid = chooseamiid(os, region)
    return upamiid(amiid, type=type, secGroup=secGroup, keys=keys, count=count, subnet=subnet)


def upamiid(amiid, type, secGroup, keys, count=1, subnet=None):
    cmd = " ec2 run-instances --image-id " + amiid + " --count " + str(
        count) + " --instance-type " + type + " --key-name " + keys
    if subnet is not None:
        cmd = cmd + " --subnet " + subnet + " --security-group-ids " + secGroup
    else:
        cmd = cmd + " --security-groups " + secGroup
    return runawstojson(cmd)


def iidFromUpJSON(upjsons):
    return [inst["InstanceId"] for inst in upjsons["Instances"]]


def nameInstance(iid, name):
    return runawstojson("ec2 create-tags --tags Key=Name,Value=" + name + " --resources " + iid)


def descInstance(iid=None):
    if iid is not None:
        return runawstojson("ec2 describe-instances --instance " + iid)
    else:
        return runawstojson("ec2 describe-instances")


def killinstance(iid, state="terminate"):
    try:
        i = descInstance(iid)
    except RuntimeError:
        raise ValueError(iid + " is not one of your instance IDs")
    if "Reservations" not in i or not len(i["Reservations"]) or "Instances" not in i["Reservations"][0] or not len(
            i["Reservations"][0]["Instances"]):
        raise ValueError(iid + " is not one of your instance IDs")
    if i["Reservations"][0]["Instances"][0]["State"]["Name"] is "terminated":
        raise ValueError(iid + " already terminated")
    return runawstojson('ec2 ' + state + '-instances --instance-ids ' + iid)


def killvolume(volID):
    descvol = runawstojson("ec2 describe-volumes --volume " + volID)
    # print descvol
    if descvol['Volumes'][0]["State"] != "available":
        raise ValueError("Volume not available to be killed " + volID)
    return runawstojson("ec2 delete-volume --volume " + volID)


def createimage(iid, aname, description):
    descim = runawstojson(
        "ec2 create-image --instance-id " + iid + " --name " + aname + " --description '" + description + "'")
    if "ImageId" not in descim:
        raise ValueError("Could not create image of " + iid)
    return str(descim["ImageId"])


def pubIP(iid):
    try:
        i = descInstance(iid)
    except RuntimeError:
        raise ValueError(iid + " is not one of your instance IDs")
    if "Reservations" not in i or not len(i["Reservations"]) or "Instances" not in i["Reservations"][0] or not len(
            i["Reservations"][0]["Instances"]):
        raise ValueError(iid + " is not one of your instance IDs")
    try:
        return i["Reservations"][0]["Instances"][0]["PublicIpAddress"]
    except KeyError:
        return None


def privIP(iid):
    try:
        i = descInstance(iid)
    except RuntimeError:
        raise ValueError(iid + " is not one of your instance IDs")
    if "Reservations" not in i or not len(i["Reservations"]) or "Instances" not in i["Reservations"][0] or not len(
            i["Reservations"][0]["Instances"]):
        raise ValueError(iid + " is not one of your instance IDs")
    try:
        return i["Reservations"][0]["Instances"][0]["PrivateIpAddress"]
    except KeyError:
        return None


def addNewEBSVol(iid, conf, access_key):
    """
    Create and name a new ebs volume, give it to a pre-existing instance and mount it on that instance

    conf is a dictionary which must contain:
    "Mount": "where-to_mount_it",   "Size" : SizeIngGB, "Attach" : "aws_expected_device_name", "Fdisk" :
    "device_name_seen_by_fdisk"
    e.g.:
    "Mount": "/opt2",   "Size" : 1, "Attach" : "/dev/sdb", "Fdisk" : "/dev/xvdb"
    Fdisk is optional, if not given it will be guessed from "Attach" and the region.
    i.e.:
    region  Attach  FDisk
    eu-*    sd<X>     xvd<X>   (e.g. sdb->xvdb)
    ap-*    sd<Y>     xvd<Y+4>  (e.g. sbd->xvdf)
    """
    try:
        i = descInstance(iid)
    except RuntimeError:
        raise ValueError(iid + " is not one of your instance IDs")
    if "Fdisk" not in conf:
        import string
        alpha = string.ascii_lowercase
        skip = 0
        if detectRegion().startswith('eu'):
            # eu-*    sd<X>     xvd<X>   (e.g. sdb->xvdb)
            skip = 0
        elif detectRegion().startswith('ap'):
            # ap-*    sd<Y>     xvd<Y+4>  (e.g. sbd->xvdf)
            skip = 4
        conf["Fdisk"] = '/dev/xvd' + alpha[alpha.index(conf["Attach"][-1]) + skip]
    ip = pubIP(iid)
    av_zone = i["Reservations"][0]["Instances"][0]["Placement"]["AvailabilityZone"]
    voljson = runawstojson("ec2 create-volume --size " + str(conf["Size"]) + " --availability-zone " + av_zone)
    instnam = ""
    for tag in i["Reservations"][0]["Instances"][0]["Tags"]:
        if tag["Key"] == "Name":
            instnam = tag["Value"]
    # print voljson
    volID = voljson["VolumeId"]
    nameInstance(volID, instnam + conf["Mount"].replace("/", "_"))
    time.sleep(5)
    count = 0
    while count < 10:
        descvol = runawstojson("ec2 describe-volumes --volume " + volID)
        # print descvol
        if descvol['Volumes'][0]["State"] == "available":
            break
        time.sleep(5)
        count = count + 1
    resjson = runawstojson(
        "ec2 attach-volume --volume-id " + volID + " --instance-id " + iid + " --device " + conf["Attach"])
    # print resjson
    time.sleep(5)
    count = 0
    while count < 10:
        descvol = runawstojson("ec2 describe-volumes --volume " + volID)
        # print descvol
        if descvol['Volumes'][0]['Attachments'][0]["State"] == "attached":
            break
        time.sleep(5)
        count = count + 1
    remote = lD.remoteHost("root", ip, access_key)
    remote.cp(os.path.dirname(__file__) + "/../remotescripts/fdiskwrap.sh", "~/fdiskwrap.sh")
    remote.run("chmod a+x fdiskwrap.sh")
    try:
        remote.run("./fdiskwrap.sh " + conf["Fdisk"])
    except RuntimeError:
        time.sleep(30)
        remote.run("./fdiskwrap.sh " + conf["Fdisk"])
    remote.run("mkfs.ext4 -b 4096 " + conf["Fdisk"] + "1 ")
    remote.run("bash -c 'echo \"" + conf["Fdisk"] + "1 " + conf["Mount"] + " ext4 defaults 1 1\" >> /etc/fstab'")
    mvto = " /" + conf["Mount"].replace("/", "_")
    remote.run("bash -c \"mv " + conf["Mount"] + mvto + "; mkdir " + conf["Mount"] + "; mount " + conf["Mount"] + ";\"")
    remote.run("bash -c \"if [ -d " + mvto + " ] ; then chmod --reference " + mvto + " " + conf["Mount"] + " ; fi\"")
    remote.run("bash -c 'shopt -s dotglob; if [ \"$(ls -A " + mvto + ")\" ] ; then mv " + mvto + "/* " + conf[
        "Mount"] + "/ ; fi'")
    res = remote.run("df -hP")
    if conf["Mount"] not in res:
        raise RuntimeError("Could not mount the requested disk, resulted in " + res)
    return True


class _addEbsVolumesThread(threading.Thread):
    """
    A threading class which locks before printing a result,
    method should be replaced with your own method returning a
    string for printing
    """

    def __init__(self, pool, lock, access_key):
        """
        pool should be a Queue.Queue object
        lock, a thread.lock object
        """
        threading.Thread.__init__(self)
        self.lock = lock
        self.pool = pool
        self.key = access_key
        self.done = False
        self.cur = None
        self.errors = []

    def run(self, limit=1000):
        """
        The main sequence, method, lock, print, unlock
        """
        # prevent truly infinite loops
        looping = 0
        while not self.done and looping < limit:
            self.cur = None
            looping = looping + 1
            try:
                item = self.pool.get_nowait()
                # self.lock.acquire()
                # print item
                # sys.__stdout__.flush()
                # self.lock.release()
                self.cur = item
                if item is not None:
                    for mount in item[1]:
                        result = addNewEBSVol(item[0], mount, self.key)
            except Queue.Empty:
                self.done = True
            except Exception as e:
                self.lock.acquire()
                print "Exiting a thread due to Error: " + str(self.cur) + " " + str(e)
                sys.__stdout__.flush()
                self.lock.release()
                err1, err2, err3 = sys.exc_info()
                self.errors.append(str(e) + " " + str(err1) + " " + str(err2) + "\n" + str(err3) + "\n" + str(self.cur))


def addEbsVolumes(iids, mounts, access_key, nthreads=20):
    """
    Add a lot of EBS volumes in parallel with threading
    iid, list of iids,
    mounts list of lists of mount point configurations to add, such as:
    [i-01dweww] [[{"Mount": "/opt2",   "Size" : 1, "Attach" : "/dev/sdb", "Fdisk" : "/dev/xvdb"}]]
    """
    # print iids, mounts
    if len(iids) != len(mounts):
        raise ValueError("length of iids must be the same as len mounts")
    # print items
    itemPool = Queue.Queue()
    for iid, mounts in zip(iids, mounts):
        # print iid, mounts
        # sys.__stdout__.flush()
        if type(mounts) is not list:
            raise TypeError("Mounts must be a _list_ of mounts...")
        if type(iid) is list:
            raise TypeError("At this point, iid should be a string!...")
        itemPool.put((iid, mounts))
    lock = thread.allocate_lock()
    thethreads = []
    for _i in range(nthreads):
        t = _addEbsVolumesThread(itemPool, lock, access_key)
        thethreads.append(t)
        t.start()
    # setup a timeout to prevent really infinite loops!
    import datetime
    import time

    begin = datetime.datetime.utcnow()
    timeout = 60 * 60 * 3
    for t in thethreads:
        while not t.done:
            if (datetime.datetime.utcnow() - begin).seconds > timeout:
                break
            time.sleep(0.1)
    nd = [t for t in thethreads if not t.done]
    errs = []
    for t in thethreads:
        errs = errs + t.errors
    if len(errs):
        raise RuntimeError("Problems creating volumes, as: \n" + '\n'.join(errs))
    if len(nd):
        raise RuntimeError("Timeout in running create volumes as threads")


def waitforstate(iid, state="running"):
    import time
    # wait until ambari server is up
    rounds = 1
    flag = False
    while rounds <= 10:
        instance = descInstance(iid)["Reservations"][0]["Instances"][0]
        if instance["State"]["Name"] is state:
            flag = True
            break
        time.sleep(60)
        rounds = rounds + 1
    if not flag:
        raise ValueError("state " + state + " not reached after 10 minutes for " + iid)
    return True


def checksecjson(json, requirefield=["SecurityGroup"], requirekeys=["AWS", "GIT", "SSH"]):
    missing = [k for k in requirefield if k not in json.keys()]
    if len(missing):
        raise IOError("Your json file is missing the following keys " + missing.__str__())
    if not len(requirekeys):
        return
    if "AccessKeys" not in json:
        raise KeyError("You must specify access keys " + requirekeys.__str__())
    missing = [k for k in requirekeys if k not in json["AccessKeys"]]
    if len(missing):
        raise IOError("Your json file keys are missing the following Access Keys " + missing.__str__())
    for key, val in json["AccessKeys"].iteritems():
        if key not in requirekeys:
            continue
        if not os.path.exists(os.path.expanduser(val["KeyFile"])):
            raise IOError("Keyfiles must exist " + val["KeyFile"])
        if "------" not in lD.runQuiet("ls -l " + val["KeyFile"]):
            raise IOError(
                "Your private keyfile " + val["KeyFile"] + " " + key + " needs to have X00 permissions (400 or 600).")
    return True


#
# VPC and cloudformation interactions
#

# def copySecurityGroupToVPC(group_from, vpc_to):
#    """
#    Add inbound security rules from one security group to another
#    """
#    _details_from=runawstojson("ec2 describe-security-groups --group-ids "+group_from)
#    print _details_from
#    for
#    #create new security group in destination
#    #copy across all rules
#    runawstojson("ec2 authorize-security-group-ingress --group-id sg-903004f8 --protocol tcp --port 22 --cidr
# 203.0.113.0/24")

def createCloudFormation(stack_name, template_script, parameters={}):
    """
    Run a cloud formation template, return the json that aws cli gives
    """
    _paramadd = ""
    for k, v in parameters.iteritems():
        _paramadd = _paramadd + " ParameterKey=" + k + ",ParameterValue=" + v
    if len(_paramadd):
        _paramadd = " --parameters " + _paramadd
    _stackinfo = runawstojson(
        "cloudformation create-stack --stack-name " + stack_name + " --template-body " + template_script + _paramadd)
    return _stackinfo


def waitForStack(stack_name, okstats=["CREATE_IN_PROGRESS", "CREATE_COMPLETE"]):
    """
    Enter a stack_name from cloud_formation, and wait for the status CREATE_COMPLETE
    """
    flag = False
    rounds = 0
    _stackinfo = None
    import time

    while rounds < 60:
        _stackinfo = runawstojson("cloudformation describe-stacks --stack-name " + stack_name)
        _cur_status = _stackinfo["Stacks"][0]["StackStatus"]
        if _cur_status not in okstats:
            # print _stackinfo["Stacks"][0]
            raise ValueError("Stack " + stack_name + " failed to create, status is " + _cur_status)
        if _cur_status == "CREATE_COMPLETE":
            flag = True
            break
        time.sleep(10)
    # print _stackinfo["Stacks"][0]
    return _stackinfo["Stacks"][0]


def addGroupToGroup(group_to_add, group_to_modify):
    """
    Whitelist one security group within a differnet security group
    """
    return runawstojson(
        "ec2 authorize-security-group-ingress --group-id " + group_to_modify
        + " --source-group " + group_to_add + " --protocol -1")
