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
This script is used to deploy a cluster based on a blueprint

deploy_from_blueprint blueprint.json cluster.json [hostname=localhost] [access_key_if_remote_or_security_config_json]
[--verbose] [--not-strict]

You only need to specify hostname when the ambari server is remote.
You only need to specify access_key if ~/.ssh/id_rsa cannot be used to access this remote ambari server
You can also specify the access key by providing a json file with "AccessKeys" : {"SSH" : {"KeyFile" : "path/to/file"}}

[--not-strict] : turn off strict host-key checking

The contents of blueprints and cluster templates are very specific, please see our wiki or the ambari wiki
https://cwiki.apache.org/confluence/display/AMBARI/Blueprints

Also you can see example .blueprint.json and matching .cluster.json files in the blueprints directory

Currently the ambari default username and password are stored in this file, but the user of the script can change
this if they wish.
"""

#############################################################
# read inputs, first a blueprint, second a cluster config,
#############################################################
import sys
import os
import json
import time

if "--help" in sys.argv or "-h" in sys.argv:
    print __doc__
    sys.exit(0)

if len(sys.argv) < 2:
    print __doc__
    raise KeyError("Not enough parameters specified")

verbose = False
if "--verbose" in sys.argv or "--debug" in sys.argv:
    sys.argv = [s for s in sys.argv if s not in ["--verbose", "--debug"]]
    verbose = True

strict = True
if "--not-strict" in sys.argv:
    sys.argv = [s for s in sys.argv if s not in ["--not-strict"]]
    strict = False

blueprintfile = sys.argv[1]
clusterfile = sys.argv[2]
thehost = "localhost"
if len(sys.argv) > 3:
    thehost = sys.argv[3]
access_key = "~/.ssh/id_rsa"
if len(sys.argv) > 4:
    access_key = sys.argv[4]

if not os.path.exists(blueprintfile):
    raise IOError("Blueprint does not exist! " + blueprintfile)
if not os.path.exists(clusterfile):
    raise IOError("Cluster configuration does not exist! " + clusterfile)
if not os.path.exists(os.path.expanduser(access_key)):
    raise IOError("Access key config does not exist! " + access_key)
try:
    jsondat = open(os.path.expanduser(access_key))
    acconf = json.loads(jsondat.read())
    jsondat.close()
    akey = acconf["AccessKeys"]["SSH"]["KeyFile"]
    access_key = akey
except:
    #either invalid json or no key in this file
    pass
if not os.path.exists(os.path.expanduser(access_key)):
    raise IOError("Access key does not exist or invalid json file provided! " + access_key)

print "testing json completeness of blueprint", blueprintfile
jsondat = open(blueprintfile)
blueprint = json.loads(jsondat.read())
jsondat.close()
print "testing json completeness of cluster", clusterfile
jsondat = open(clusterfile)
cluster = json.loads(jsondat.read())
jsondat.close()
hosts = []
sys.stdout.flush()
if "Blueprints" not in blueprint:
    raise ValueError("blueprint file does not give itself a name, is this the right file? " + blueprintfile)
if "host_groups" not in cluster:
    raise ValueError("cluster file does not define any host groups, is this the right file? " + clusterfile)
for group in cluster["host_groups"]:
    for host in group["hosts"]:
        if host["fqdn"] not in hosts:
            hosts.append(host["fqdn"])

#Check that the blueprint is what is asked for in the cluster config...
if blueprint["Blueprints"]["blueprint_name"] != cluster["blueprint"]:
    raise ValueError("You've not asked for a cluster which uses this blueprint... try again!")

for host in hosts:
    if host.lower() != host:
        raise NameError(
            "Ambari currently does not fully support host names with capital letters in them, you will need to fix "
            "this, sorry!")

installfrom = os.path.realpath(os.path.dirname(__file__))
liblocation = os.path.realpath(installfrom + '/lib')
sys.path.append(liblocation)

import kavedeploy as lD

lD.debug = verbose
lD.strict_host_key_checking = strict
lD.testproxy()

print "check that Ambari @" + thehost + " is reachable"
if lD.which("curl") is None:
    raise NameError("Please install curl locally for this check! (e.g. yum -y install curl)")
lD.runQuiet("curl --user admin:admin http://" + thehost + ":8080/api/v1/clusters")

##################################################################
# Start ambari agents
##################################################################

print "Attempting to start ambari agents on all", len(hosts), "nodes"
sys.stdout.flush()

ambari = lD.remoteHost("root", thehost, access_key)

#Step one, install myself, dsh and deploy ambari agents to all nodes
try:
    ambari.run("which pdsh")
    ambari.run("which curl")
except RuntimeError:
    ambari.run("yum -y install pdsh curl")

ambari.run("service iptables stop")

admin = ambari.run("hostname")

whole_cluster = lD.multiremotes(hosts, jump=ambari)

#Check if all nodes in the cluster are contactable
try:
    whole_cluster.check(firsttime=True)
except RuntimeError:
    print "Could not access machines with passwordless ssh, the ambari node must have passwordless ssh access to the " \
          "rest, fix and try again"
    raise

#Verify that all nodes have similar system times
ambtime=int(ambari.run("date -u '+%s'"))
cltime=whole_cluster.run("date -u '+%s'")
cltime=[(int(p.split(':')[-1])) for p in cltime.split('\n')]

if (max(cltime)-min(cltime))>(10*60):
   raise RuntimeError('The system clocks are not synchronized, a difference of '+str(max(cltime)-min(cltime))+' seconds was found')
if min(cltime)<(ambtime-5):
   raise RuntimeError('At least one machine has a too early system clock, a difference of '+str(ambtime-min(cltime))+' seconds was found')

try:
    if "no ambari-agent" in whole_cluster.run("which ambari-agent"):
        raise RuntimeError()
except RuntimeError:
    whole_cluster.register()
    whole_cluster.run("yum -y install epel-release")
    #TODO: instead copy this file _from_ the ambari node *to* the others!
    # For the time being, copy to tmp, distribute if necessary
    copy_from = None
    for _repoption in ["/etc/yum.repos.d/ambari.repo", installfrom + "/repo/ambari.repo",
                       installfrom + "/../dev/repo/ambari.repo"]:
        if os.path.exists(_repoption) and os.access(_repoption, os.R_OK):
            copy_from = _repoption
            break
    if copy_from is None:
        raise IOError("Could not find local ambari.repo file!")
    whole_cluster.cp(copy_from, "/tmp/ambari.repo")
    whole_cluster.run(
        "\"bash -c 'if [ ! -e /etc/yum.repos.d/ambari.repo ] ; then cp /tmp/ambari.repo /etc/yum.repos.d/ambari.repo "
        "; fi; rm -f /tmp/ambari.repo ;'\"")
    try:
        #try and retry
        whole_cluster.run("yum -y install ambari-agent curl wget")
    except RuntimeError:
        time.sleep(5)
        whole_cluster.run("yum -y install epel-release ambari-agent curl wget")

try:
    whole_cluster.cp(liblocation + "/../remotescripts/set_ambari_node.py", "set_ambari_node.py")
except RuntimeError:
    whole_cluster.register()
    whole_cluster.cp(liblocation + "/../remotescripts/set_ambari_node.py", "set_ambari_node.py")

#turn off se linux across the cluster ...
whole_cluster.run("'echo 0 >/selinux/enforce'")
whole_cluster.run("python set_ambari_node.py " + admin)
try:
    whole_cluster.run("ambari-agent restart")
except RuntimeError:
    time.sleep(2)
    whole_cluster.run("ambari-agent stop")
    time.sleep(2)
    whole_cluster.run("ambari-agent start")
time.sleep(5)

#Modify permissions of installed ambari agent components
whole_cluster.run('"bash -c \\"if [ -d /var/lib/ambari-agent/data ]; then mkdir -p /var/lib/ambari-agent/tmp; chmod -R 0600 /var/lib/ambari-agent/data;'
                  'chmod -R a+X /var/lib/ambari-agent/data; chmod -R a+rx /var/lib/ambari-agent/data/tmp; fi;\\""')
whole_cluster.run('"bash -c \\"if ls /var/lib/ambari-agent/keys/*.key 1>/dev/null 2>&1; then chmod 0600 /var/lib/ambari-agent/keys/*.key; fi\\""')

##################################################################
# Check that all hosts exist now
##################################################################
ok = False
missing = []
count = 0
while count < 10:
    reghosts = lD.runQuiet("curl --user admin:admin http://" + thehost + ":8080/api/v1/hosts")
    missing = [host for host in hosts if host not in reghosts]
    if not len(missing):
        ok = True
        break
    count = count + 1
    time.sleep(5)
if not ok:
    print reghosts
    raise RuntimeError(
        "Registration Error, the hosts" + missing.__str__() + " do not exist, try curl --user admin:admin http://" +
        thehost + ":8080/api/v1/hosts")

#Modify permissions of installed ambari agent components
whole_cluster.run('"bash -c \\"if [ -d /var/lib/ambari-agent/data ]; then mkdir -p /var/lib/ambari-agent/tmp; chmod -R 0600 /var/lib/ambari-agent/data;'
                  'chmod -R a+X /var/lib/ambari-agent/data; chmod -R a+rx /var/lib/ambari-agent/data/tmp; fi;\\""')
whole_cluster.run('"bash -c \\"if ls /var/lib/ambari-agent/keys/*.key 1>/dev/null 2>&1; then chmod 0600 /var/lib/ambari-agent/keys/*.key; fi\\""')

##################################################################
# Add pdsh groups, for all hostgroups
##################################################################
# for entire cluster
clustername=clusterfile.split(os.sep)[-1].split('.')[0]
ambari.run('mkdir -p ~/.dsh/group')
for host in hosts:
    ambari.run("echo "+host+" >> "+"~/.dsh/group/"+clustername)
#for each hostgroup
for group in cluster["host_groups"]:
    hgname=group["name"]
    for host in group["hosts"]:
        ambari.run("echo "+host["fqdn"]+" >> "+"~/.dsh/group/"+clustername+"_"+hgname)

##################################################################
# Register blueprint and cluster template
##################################################################
print "Attempting to register blueprint ", blueprint["Blueprints"]["blueprint_name"], " and create cluster ", clustername

sys.stdout.flush()

#next, register blueprint by name to the ambari server
regcmd = "curl --user admin:admin -H 'X-Requested-By:ambari' -X POST http://" + thehost + ":8080/api/v1/blueprints/" + \
         blueprint["Blueprints"]["blueprint_name"] + "?validate_topology=false -d @" + os.path.expanduser(blueprintfile)
regblueprint = lD.runQuiet(regcmd)
if verbose:
    print regblueprint
if "Server Error" in regblueprint:
    if not verbose:
        print regblueprint
    print "Warning: detected server error registering blueprint, trying server restart"
    ambari.run("ambari-server restart")
    regblueprint = lD.runQuiet(regcmd)
    if verbose:
        print regblueprint
elif "specified stack doesn't exist" in regblueprint:
    print regblueprint
    raise NameError(
        "Detected error, unable to find this stack, did you run patch.sh and restart the server as required?")


# Check if blueprint exists before continuing
registered = "curl --user admin:admin -H 'X-Requested-By:ambari' -X GET http://" + thehost + ":8080/api/v1/blueprints/"
registered = lD.runQuiet(registered)
if blueprint["Blueprints"]["blueprint_name"] not in registered:
    print regblueprint
    raise RuntimeError(
        "Blueprint does not exist, take a look yourself with " + "curl --user admin:admin http://" + thehost +
        ":8080/api/v1/blueprints/")

#then add the cluster definition, should start all the processes
regcmd = "curl --user admin:admin -H 'X-Requested-By:ambari' -X POST http://" + thehost + ":8080/api/v1/clusters/" + \
         clustername + " -d @" + os.path.expanduser(clusterfile)
regcluster = lD.runQuiet(regcmd)
if verbose:
    print regcluster
if "Server Error" in regcluster:
    if not verbose:
        print regcluster
    print "Warning: detected server error, trying server restart"
    ambari.run("ambari-server restart")
    regcluster = lD.runQuiet(regcmd)
    if verbose:
        print regcluster
if "Unable to update" in regcluster:
    if not verbose:
        print regcluster
    print >> sys.stderr, "Error detected in spooling up cluster from template, is the template complete? Are you " \
                         "missing required services?"
    sys.exit(1)
if "InProgress" not in regcluster:
    if not verbose:
        print regcluster
    print >> sys.stderr, "Detected error registering cluster"
    sys.exit(1)

print "Registration successful, configuration in progress, monitor through the web interface at http://" + thehost + ":8080"
print "check clusters with curl --user admin:admin http://" + thehost + ":8080/api/v1/clusters"
print "check hosts with curl --user admin:admin http://" + thehost + ":8080/api/v1/hosts"
