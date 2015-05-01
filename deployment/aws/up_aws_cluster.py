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
create a cluster within a pre-existing security group

usage up_new_cluster.py cluster_name cluster_config.json [security_config.json] [--verbose]

these 3 options are required:
    cluster_name: name of the cluster to create
    cluster_config.json: a json file with the configuration (see readme for details)

optional:
    security_config.json : a json file with the security group/subnet-id keypair/keyfile (see readme for details). If
    not set I will follow the AWSSECCONF environment variable.
    --verbose : print all remotely running commands
    --not-strict : turn off strict host-key checking
"""

import sys
import os
import json

instancegroups = {}

installfrom = os.path.realpath(os.path.dirname(__file__))
liblocation = os.path.realpath(installfrom + '/../lib')
sys.path.append(liblocation)

import libDeploy as lD
import libAws as lA
import json

lA.testaws()

if lD.detect_proxy() and lD.proxy_blocks_22:
    raise SystemError(
        "This proxy blocks port 22, that means you can't ssh to your machines to do the initial configuration. To "
        "skip this check set libDeploy.proxy_blocks_22 to false and libDeploy.proxy_port=22")

lD.testproxy()


def help():
    print __doc__
    #sys.exit(code)


def checkOpts():
    if "-h" in sys.argv or "--help" in sys.argv:
        help()
        sys.exit(0)
    if "--verbose" in sys.argv:
        lD.debug = True
        sys.argv = [s for s in sys.argv if s != "--verbose"]
    else:
        lD.debug = False
    if "--not-strict" in sys.argv:
        sys.argv = [s for s in sys.argv if s not in ["--not-strict"]]
        lD.strict_host_key_checking = False
    if len(sys.argv) < 3:
        help()
        raise AttributeError("You did not supply enough parameters")
    if len(sys.argv) > 5:
        help()
        raise AttributeError("You supplied too many parameters")
    if not os.path.exists(os.path.expanduser(sys.argv[2])):
        raise IOError("json config file must exist " + sys.argv[2])


checkOpts()

cluster_name = sys.argv[1]
jsondat = open(os.path.expanduser(sys.argv[2]))
cluster_config = json.loads(jsondat.read())
jsondat.close()

keyfile = ""

if len(sys.argv) > 3:
    keyfile = os.path.expanduser(sys.argv[3])
else:
    if "AWSSECCONF" not in os.environ:
        print __doc__
        raise IOError("please specify keyfile or set AWSSECCONF environment variable!")
    keyfile = os.path.expanduser(os.environ["AWSSECCONF"])

if not os.path.exists(os.path.expanduser(keyfile)):
    raise IOError("security config file must exist " + keyfile)

jsondat = open(keyfile)
security_config = json.loads(jsondat.read())
jsondat.close()
lA.checksecjson(security_config, requirekeys=["AWS", "SSH"])
security_group = security_config["SecurityGroup"]
amazon_keyfile = security_config["AccessKeys"]["AWS"]["KeyFile"]
amazon_keypair_name = security_config["AccessKeys"]["AWS"]["KeyName"]
gitenv = None
git = False
if "GIT" in security_config["AccessKeys"]:
    git = True
    gitenv = github_keyfile = security_config["AccessKeys"]["GIT"]
subnet = None
if "Subnet" in security_config.keys():
    subnet = security_config["Subnet"]

dnsiid = None

if "CloudFormation" in cluster_config:
    print "============================================"
    print "Create a new VPC from cloud formation script"
    print "============================================"
    sys.stdout.flush()
    #replace default keys with those from the security config file?
    import datetime

    _vpc_name = cluster_name + "-" + amazon_keypair_name + "-" + datetime.datetime.utcnow().strftime("%Y%m%d%H%M")
    lA.createCloudFormation(_vpc_name, cluster_config["CloudFormation"]["Script"],
                            parameters={"KeyName": amazon_keypair_name, "VPCNAME": _vpc_name})
    _info = lA.waitForStack(_vpc_name)
    #print _info["Outputs"]
    for _output in _info["Outputs"]:
        if _output['OutputKey'] == "SubnetId":
            subnet = _output['OutputValue']
        elif _output['OutputKey'] == "SecurityGroupId":
            security_group = _output['OutputValue']
        elif _output['OutputKey'] == "DNSId":
            dnsiid = _output['OutputValue']
    #authorize group members to see themselves
    #print security_group, subnet, dnsiid
    lA.addGroupToGroup(security_group, security_group)
    #auto assign public IPs here
    lA.runawstojson("ec2 modify-subnet-attribute --subnet-id " + subnet + " --map-public-ip-on-launch")
    print "Created stack:", _vpc_name
    #sys.exit(1)

print "===================================="
print "up the instance groups"
print "===================================="
sys.stdout.flush()

for instancegroup in cluster_config["InstanceGroups"]:
    count = instancegroup["Count"]
    autoname = True
    if count < 0:
        count = 1
        autoname = False
    if count == 0:
        continue
    up = lA.upCentos6(type=instancegroup["InstanceType"], secGroup=security_group, keys=amazon_keypair_name,
                      count=count, subnet=subnet)
    instancegroups[instancegroup["Name"]] = lA.iidFromUpJSON(up)

instance_to_remote = {}

print "Created IIDs:", instancegroups

print "===================================="
print "wait for them all to be up"
print "===================================="
sys.stdout.flush()
import time

time.sleep(5)
for k, ig in instancegroups.iteritems():
    for iid in ig:
        ip = None
        acount = 0
        while (ip is None and acount < 10):
            try:
                ip = lA.pubIP(iid)
            except ValueError:
                pass
            if ip is None:
                print "waiting for IP"
                lD.mysleep(1)
            acount = acount + 1
        if ip is None:
            raise SystemError(iid + " no ip assigned after quite some time")
        remote = lD.remoteHost("root", ip, amazon_keyfile)
        lD.waitUntilUp(remote, 20)
        remote.register()
        instance_to_remote[iid] = remote

allremotes = ["ssh:root@" + remote.host for remote in instance_to_remote.values()]
allremotes = lD.multiremotes(list_of_hosts=allremotes, access_key=amazon_keyfile)
print "test PDSH"
print allremotes.run("echo yes")

print "===================================="
print "name the instances"
print "===================================="
sys.stdout.flush()
instance_to_name = {}

for instancegroup in cluster_config["InstanceGroups"]:
    count = instancegroup["Count"]
    autoname = True
    if count < 0:
        autoname = False
    if not autoname:
        instance_to_name[instancegroups[instancegroup["Name"]][0]] = instancegroup["Name"]
        lA.nameInstance(instancegroups[instancegroup["Name"]][0], cluster_name + '-' + instancegroup["Name"])
        continue
    for num, instance in enumerate(instancegroups[instancegroup["Name"]]):
        instance_to_name[instance] = instancegroup["Name"] + ("-%03d" % (num + 1))
        lA.nameInstance(instance, cluster_name + '-' + instancegroup["Name"] + ("-%03d" % (num + 1)))

#Also name the attached volumes
for instance, iname in instance_to_name.iteritems():
    idesc = lA.descInstance(instance)
    vols = idesc["Reservations"][0]["Instances"][0]["BlockDeviceMappings"]
    for v in vols:
        if "Ebs" in v and "DeviceName" in v:
            lA.nameInstance(v["Ebs"]["VolumeId"], cluster_name + '-' + iname + v["DeviceName"].replace("/", "_"))

#TODO: use a proper dns configuration here instead of writing into the host file
print "=============================================="
print "Configure machine names"
print "=============================================="
sys.stdout.flush()
for instance, remote in instance_to_remote.iteritems():
    domainName = 'kave.io'
    if "Domain" in cluster_config:
        domainName = cluster_config["Domain"]["Name"]
    #print "configuring", remote.host, "->", instance_to_name[instance]
    lD.renameRemoteHost(remote, instance_to_name[instance].lower(), domainName)
    if domainName=="kave.io":
        allremotes.run("mkdir -p /etc/kave/")
        allremotes.run("'/bin/echo http://repos:kaverepos@repos.dna.kpmglab.com/ >> /etc/kave/mirror'")

if dnsiid is not None:
    print "============================================"
    print "add to reverse lookup on DNS"
    print "============================================"
    domainName = 'kave.io'
    if "Domain" in cluster_config:
        domainName = cluster_config["Domain"]["Name"]
    ip = lA.pubIP(dnsiid)
    privip = lA.privIP(dnsiid)
    #print ip, privip
    dnsserv = lD.remoteHost("root", ip, amazon_keyfile)
    lD.waitUntilUp(dnsserv, 20)
    dnsserv.register()
    date = dnsserv.run('date "+%Y%m%d%H%M"').strip()
    nameandprivip = []
    nameandprivip = [(name, lA.privIP(instance)) for instance, name in instance_to_name.iteritems()]
    #print nameandprivip
    forward = """$TTL 86400
@   IN  SOA     ns.%DOMAIN%. root.%DOMAIN%. (
        %DATE%  ;Serial
        3600      ;Refresh
        1800      ;Retry
        604800    ;Expire
        86400     ;Minimum TTL
)

; Specify our nameservers
        IN      NS      ns.%DOMAIN%.
; Resolve nameserver hostnames to IP, replace with your two droplet IP addresses.
ns     IN      A       %PRIVATE%

; Define hostname -> IP pairs which you wish to resolve
repos IN A 94.143.213.26
""".replace("%DOMAIN%", domainName).replace("%PRIVATE%", privip).replace("%DATE%", date)
    reverse = """$TTL 86400
@   IN  SOA     ns.%DOMAIN%. root.%DOMAIN%. (
        %DATE%  ;Serial
        3600      ;Refresh
        1800      ;Retry
        604800    ;Expire
        86400     ;Minimum TTL
)

; Specify our nameservers
        IN      NS      ns.%DOMAIN%.
; Resolve nameserver hostnames to IP, replace with your two droplet IP addresses.
ns     IN      A       %PRIVATE%

; Define hostname -> IP pairs which you wish to resolve
%PRIVATE%.in-addr.arpa. IN PTR ns.%DOMAIN%.
""".replace("%DOMAIN%", domainName).replace("%PRIVATE%", '.'.join(reversed(privip.split('.')))).replace("%DATE%", date)
    forward = forward + '\n' + '\n'.join([n + " IN A " + ip for n, ip in nameandprivip])
    reverse = reverse + '\n' + '\n'.join(
        ['.'.join(reversed(ip.split('.'))) + ".in-addr.arpa. IN PTR " + n + "." + domainName + "." for n, ip in
         nameandprivip])
    #write into temp local file and then copy it
    ff = open("/tmp/forward" + domainName + dnsiid, 'w')
    ff.write(forward)
    ff.close()
    rf = open("/tmp/reverse" + domainName + dnsiid, 'w')
    rf.write(reverse)
    rf.close()
    #print forward
    #print reverse
    dnsserv.cp("/tmp/forward" + domainName + dnsiid, "/var/named/forward." + domainName)
    dnsserv.cp("/tmp/reverse" + domainName + dnsiid, "/var/named/reverse." + domainName)
    lD.runQuiet("rm -rf /tmp/reverse" + domainName + dnsiid)
    lD.runQuiet("rm -rf /tmp/forward" + domainName + dnsiid)
    dnsserv.run("service named restart")

print "=============================================="
print "Configure /etc/hosts ",
if dnsiid is None:
    print
else:
    print "(as backup)"
print "=============================================="
sys.stdout.flush()
#write into etc/hosts file for all machines
for instance, remote in instance_to_remote.iteritems():
    for otherinstance, othername in instance_to_name.iteritems():
        #if otherinstance==instance:
        #    continue
        lD.addAsHost(edit_remote=remote, add_remote=instance_to_remote[otherinstance],
                     dest_internal_ip=lA.privIP(otherinstance))

print "==================================="
print "add any extra disk space (parallelized per instance)"
print "==================================="
sys.stdout.flush()
adtoiids = []
admounts = []
for instancegroup in cluster_config["InstanceGroups"]:
    if "ExtraDisks" in instancegroup:
        for instance in instancegroups[instancegroup["Name"]]:
            admounts.append(instancegroup["ExtraDisks"])
            adtoiids.append(instance)
lA.addEbsVolumes(adtoiids, admounts, amazon_keyfile)
#        #for conf in instancegroup["ExtraDisks"]:
#        #    for instance in instancegroups[instancegroup["Name"]]:
#        #        lA.addNewEBSVol(instance, conf, amazon_keyfile)


print "==================================="
print "Configure any gateways (takes time due to yum install)"
print "==================================="
sys.stdout.flush()
for instancegroup in cluster_config["InstanceGroups"]:
    if instancegroup["AccessType"] == "gateway":
        #print "found group", instancegroup["Name"]
        for instance in instancegroups[instancegroup["Name"]]:
            #print "found instance"+instance
            lD.confremotessh(instance_to_remote[instance])

print "=============================================="
print "Configure the admin to have keys to the rest"
print "=============================================="
sys.stdout.flush()
for instancegroup in cluster_config["InstanceGroups"]:
    if instancegroup["AccessType"] == "admin":
        #print "found group", instancegroup["Name"]
        for instance in instancegroups[instancegroup["Name"]]:
            #print "found instance"+instance
            for otherinstance in instance_to_remote:
                if otherinstance:
                    #give itself also keyless root access to itself!
                    lD.configureKeyless(instance_to_remote[instance], instance_to_remote[otherinstance],
                                        lA.privIP(otherinstance), preservehostname=True)

print "=============================================="
print "Add ambari to admin node"
print "=============================================="
sys.stdout.flush()
for instancegroup in cluster_config["InstanceGroups"]:
    if instancegroup["AccessType"] == "admin":
        #print "found group", instancegroup["Name"]
        for instance in instancegroups[instancegroup["Name"]]:
            #lD.confremotessh(instance_to_remote[instance])
            lD.deployOurSoft(instance_to_remote[instance], git=git, gitenv=gitenv, pack="ambarikave")

print "=============================================="
print "Turn off SE linux and IPTables (yeah, I know)"
print "=============================================="
allremotes.run("service iptables stop")
allremotes.run("'/bin/echo 0 > /selinux/enforce'")

print "==================================="
donedict = {}
for instance, name in instance_to_name.iteritems():
    donedict[name] = (instance, instance_to_remote[instance].host)
    print name,
    instance_to_remote[instance].describe()
print "Complete, created:", donedict
print "==================================="
