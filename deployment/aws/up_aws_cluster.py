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
    --this-branch : read what this branch is called and deploy software direct from this branch
"""

import sys
import os
import json

instancegroups = {}

installfrom = os.path.realpath(os.path.dirname(__file__))
liblocation = os.path.realpath(installfrom + '/../lib')
sys.path.append(liblocation)

import kavedeploy as lD
import kaveaws as lA
import json

lA.testaws()

if lD.detect_proxy() and lD.proxy_blocks_22:
    raise SystemError(
        "This proxy blocks port 22, that means you can't ssh to your machines to do the initial configuration. To "
        "skip this check set kavedeploy.proxy_blocks_22 to false and kavedeploy.proxy_port=22")

lD.testproxy()


def help():
    print __doc__
    # sys.exit(code)

version = "latest"


def check_opts():
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
    if "--this-branch" in sys.argv:
        sys.argv = [s for s in sys.argv if s not in ["--this-branch"]]
        global version
        version = lD.run_quiet("bash -c \"cd " + os.path.dirname(__file__) + "; git branch | sed -n '/\* /s///p'\"")
        stdout = lD.run_quiet("bash -c 'cd " + os.path.dirname(__file__) + "; git branch -r;'")
        if not ("origin/" + version in [s.strip() for s in stdout.split() if len(s.strip())]):
            raise NameError("There is no remote branch called "
                            + version
                            + " push your branch back to the origin and try again")
    if len(sys.argv) < 3:
        help()
        raise AttributeError("You did not supply enough parameters")
    if len(sys.argv) > 5:
        help()
        raise AttributeError("You supplied too many parameters")
    if not os.path.exists(os.path.expanduser(sys.argv[2])):
        raise IOError("json config file must exist " + sys.argv[2])


check_opts()

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

# Check that pdsh is locally installed
try:
    lD.run_quiet('which pdsh')
except lD.ShellExecuteError:
    raise SystemError('pdsh is not installed, please install pdsh first. Pdsh is useful to speed up large deployments.')

dnsiid = None
vpcid = None

if "CloudFormation" in cluster_config:
    print "============================================"
    print "Create a new VPC from cloud formation script"
    print "============================================"
    sys.stdout.flush()
    # replace default keys with those from the security config file?
    import datetime

    _vpc_name = cluster_name + "-" + \
        amazon_keypair_name.replace('_', '') + "-" + datetime.datetime.utcnow().strftime("%Y%m%d%H%M")
    lA.create_cloud_formation(_vpc_name, cluster_config["CloudFormation"]["Script"],
                              parameters={"KeyName": amazon_keypair_name, "VPCNAME": _vpc_name})
    _info = lA.wait_for_stack(_vpc_name)
    # print _info["Outputs"]
    for _output in _info["Outputs"]:
        if _output['OutputKey'] == "SubnetId":
            subnet = _output['OutputValue']
        elif _output['OutputKey'] == "SecurityGroupId":
            security_group = _output['OutputValue']
        elif _output['OutputKey'] == "DNSId":
            dnsiid = _output['OutputValue']
        elif _output['OutputKey'] == "VPCId":
            vpcid = _output['OutputValue']
    # authorize group members to see themselves
    # print security_group, subnet, dnsiid
    lA.add_group_to_group(security_group, security_group)
    # auto assign public IPs here
    lA.runawstojson("ec2 modify-subnet-attribute --subnet-id " + subnet + " --map-public-ip-on-launch")
    print "Created stack:", _vpc_name
    if "Tags" in security_config and vpcid:
        resources = lA.find_all_child_resources(vpcid)
        lA.tag_resources(resources, security_config["Tags"])
    # sys.exit(1)

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
    up = lA.up_default(type=lA.chooseinstancetype(instancegroup["InstanceType"]),
                       security_group=security_group, keys=amazon_keypair_name,
                       count=count, subnet=subnet)
    instancegroups[instancegroup["Name"]] = lA.iid_from_up_json(up)

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
                ip = lA.pub_ip(iid)
            except ValueError:
                pass
            if ip is None:
                print "waiting for IP"
                lD.mysleep(1)
            acount = acount + 1
        if ip is None:
            raise SystemError(iid + " no ip assigned after quite some time")

        remoteuser = lA.default_usernamedict[lA.default_os]
        remote = lD.remoteHost(remoteuser, ip, amazon_keyfile)

        lD.wait_until_up(remote, 20)
        remote = lD.remote_cp_authkeys(remote, 'root')
        if "Tags" in security_config:
            resources = lA.find_all_child_resources(iid)
            lA.tag_resources(resources, security_config["Tags"])
        remote.register()
        instance_to_remote[iid] = remote

allremotes = ["ssh:root@" + remote.host for remote in instance_to_remote.values()]
allremotes = lD.multiremotes(list_of_hosts=allremotes, access_key=amazon_keyfile)
print "test local PDSH, install pdcp"
print allremotes.run("echo yes")
allremotes.run("yum -y install epel-release")
allremotes.run("yum clean all")
allremotes.run("yum -y install pdsh")

print "===================================="
print "configure SSH on all machines"
print "===================================="
lD.confallssh(allremotes)

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
        lA.name_resource(instancegroups[instancegroup["Name"]][0], cluster_name + '-' + instancegroup["Name"])
        continue
    for num, instance in enumerate(instancegroups[instancegroup["Name"]]):
        instance_to_name[instance] = instancegroup["Name"] + ("-%03d" % (num + 1))
        lA.name_resource(instance, cluster_name + '-' + instancegroup["Name"] + ("-%03d" % (num + 1)))

# Also name the attached volumes
for instance, iname in instance_to_name.iteritems():
    idesc = lA.desc_instance(instance)
    vols = idesc["Reservations"][0]["Instances"][0]["BlockDeviceMappings"]
    for v in vols:
        if "Ebs" in v and "DeviceName" in v:
            lA.name_resource(v["Ebs"]["VolumeId"], cluster_name + '-' + iname + v["DeviceName"].replace("/", "_"))

# TODO: use a proper dns configuration here instead of writing into the host file
print "=============================================="
print "Configure machine names"
print "=============================================="
sys.stdout.flush()
remotes_to_name = {remote: instance_to_name[instance].lower() for instance, remote in instance_to_remote.iteritems()}
# for instance, remote in instance_to_remote.iteritems():
domain_name = 'kave.io'
if "Domain" in cluster_config:
    domain_name = cluster_config["Domain"]["Name"]
    # print "configuring", remote.host, "->", instance_to_name[instance]
lD.rename_remote_hosts(remotes_to_name, domain_name)

if domain_name == "kave.io":
    allremotes.run("mkdir -p /etc/kave/")
    allremotes.run("'/bin/echo http://repos:kaverepos@repos.dna.kpmglab.com/ >> /etc/kave/mirror'")

if dnsiid is not None:
    print "============================================"
    print "add to reverse lookup on DNS"
    print "============================================"
    domain_name = 'kave.io'
    if "Domain" in cluster_config:
        domain_name = cluster_config["Domain"]["Name"]
    ip = lA.pub_ip(dnsiid)
    priv_ip = lA.priv_ip(dnsiid)
    # print ip, priv_ip
    dnsserv = lD.remoteHost("root", ip, amazon_keyfile)
    lD.wait_until_up(dnsserv, 20)
    dnsserv.register()
    date = dnsserv.run('date "+%Y%m%d%H%M"').strip()
    nameandpriv_ip = []
    nameandpriv_ip = [(name, lA.priv_ip(instance)) for instance, name in instance_to_name.iteritems()]
    # resolve repos server
    repos = lD.run_quiet('host repos.kave.io')
    if repos.startswith("repos.kave.io has address "):
        repos = repos[len("repos.kave.io has address "):]
    else:
        repos = '94.143.213.26'
    # print nameandpriv_ip
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
repos IN A %REPOS%
""".replace("%DOMAIN%", domain_name).replace("%PRIVATE%", priv_ip).replace("%DATE%", date).replace("%REPOS%", repos)
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
""".replace("%DOMAIN%",
            domain_name).replace("%PRIVATE%",
                                 '.'.join(reversed(priv_ip.split('.')))).replace("%DATE%",
                                                                                 date)
    forward = forward + '\n' + '\n'.join([n + " IN A " + ip for n, ip in nameandpriv_ip])
    reverse = reverse + '\n' + '\n'.join(
        ['.'.join(reversed(ip.split('.'))) + ".in-addr.arpa. IN PTR " + n + "." + domain_name + "." for n, ip in
         nameandpriv_ip])
    # write into temp local file and then copy it
    ff = open("/tmp/forward" + domain_name + dnsiid, 'w')
    ff.write(forward)
    ff.close()
    rf = open("/tmp/reverse" + domain_name + dnsiid, 'w')
    rf.write(reverse)
    rf.close()
    # print forward
    # print reverse
    dnsserv.cp("/tmp/forward" + domain_name + dnsiid, "/var/named/forward." + domain_name)
    dnsserv.cp("/tmp/reverse" + domain_name + dnsiid, "/var/named/reverse." + domain_name)
    lD.run_quiet("rm -rf /tmp/reverse" + domain_name + dnsiid)
    lD.run_quiet("rm -rf /tmp/forward" + domain_name + dnsiid)
    dnsserv.run("service named restart")

print "=============================================="
print "Configure /etc/hosts ",
if dnsiid is None:
    print
else:
    print "(as backup)"
print "=============================================="
sys.stdout.flush()
# write into etc/hosts file for all machines
for otherinstance, othername in instance_to_name.iteritems():
    # if otherinstance==instance:
    #    continue
    lD.add_as_host(edit_remote=allremotes, add_remote=instance_to_remote[otherinstance],
                   dest_internal_ip=lA.priv_ip(otherinstance))

print "==================================="
print "Configure any gateways (takes time due to yum install)"
print "==================================="
sys.stdout.flush()
gateways = []
for instancegroup in cluster_config["InstanceGroups"]:
    if instancegroup["AccessType"] == "gateway":
        # print "found group", instancegroup["Name"]
        for instance in instancegroups[instancegroup["Name"]]:
            # print "found instance"+instance
            gateways.append(instance_to_remote[instance])

if len(gateways):
    gateways = ["ssh:root@" + remote.host for remote in gateways]
    gateways = lD.multiremotes(list_of_hosts=gateways, access_key=amazon_keyfile)
    lD.confremotessh(gateways)

print "=============================================="
print "Configure the admin to have keys to the rest"
print "=============================================="
sys.stdout.flush()
for instancegroup in cluster_config["InstanceGroups"]:
    if instancegroup["AccessType"] == "admin":
        # print "found group", instancegroup["Name"]
        for instance in instancegroups[instancegroup["Name"]]:
            # print "found instance"+instance
            for otherinstance in instance_to_remote:
                if otherinstance:
                    # give itself also keyless root access to itself!
                    lD.configure_keyless(instance_to_remote[instance], instance_to_remote[otherinstance],
                                         lA.priv_ip(otherinstance), preservehostname=True)

print "=============================================="
print "Turn off SE linux and IPTables (yeah, I know)"
print "=============================================="

if instance_to_remote.values()[0].detect_linux_version() in ["Centos6"]:
    allremotes.run("'echo 0 >/selinux/enforce'")
    allremotes.run("service iptables stop")
elif instance_to_remote.values()[0].detect_linux_version() in ["Centos7"]:
    allremotes.run("setenforce permissive")

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
lA.add_ebs_volumes(adtoiids, admounts, amazon_keyfile)
#        #for conf in instancegroup["ExtraDisks"]:
#        #    for instance in instancegroups[instancegroup["Name"]]:
#        #        lA.add_new_ebs_vol(instance, conf, amazon_keyfile)

print "=============================================="
print "Add ambari to admin node"
print "=============================================="
sys.stdout.flush()
for instancegroup in cluster_config["InstanceGroups"]:
    if instancegroup["AccessType"] == "admin":
        # print "found group", instancegroup["Name"]
        for instance in instancegroups[instancegroup["Name"]]:
            # lD.confremotessh(instance_to_remote[instance])
            lD.deploy_our_soft(instance_to_remote[instance], git=git, gitenv=gitenv, pack="ambarikave", version=version)

if "Tags" in security_config and vpcid:
    print "=============================================="
    print "Tag full VPC"
    print "=============================================="
    resources = lA.find_all_child_resources(vpcid)
    lA.tag_resources(resources, security_config["Tags"])

print "==================================="
donedict = {}
for instance, name in instance_to_name.iteritems():
    donedict[name] = (instance, instance_to_remote[instance].host)
    print name,
    instance_to_remote[instance].describe()
print "Complete, created:", donedict
print "==================================="
