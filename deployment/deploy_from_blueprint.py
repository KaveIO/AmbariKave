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
import requests
from requests.auth import HTTPBasicAuth
import copy
import tempfile

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
    # either invalid json or no key in this file
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

# Check that the blueprint is what is asked for in the cluster config...
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


def _r2j(res):
    """
    A simple function for extracting the json automatically from a
    request response, and raising an exception
    in the case of HTTP error code
    """
    if res.status_code not in [200, 302]:
        res.raise_for_status()
    try:
        return copy.deepcopy(res.json())
    except ValueError:
        return {}


def ambari_get(apath, ambhost=None, port=8080,
               user='admin', passwd='admin', prot='http://', api='/api/v1/'):
    """
    Wrapper round the requests framework to make calls to the local ambari server
    """
    if ambhost is None:
        ambhost = thehost
    url = prot + ambhost + ':' + str(port) + api + apath
    # print url
    req = requests.get(url, auth=HTTPBasicAuth(user, passwd), headers={'X-Requested-By': 'ambari'})
    return _r2j(req)


def ambari_post(apath, ambhost=None, data={}, port=8080,
                user='admin', passwd='admin', prot='http://', api='/api/v1/'):
    """
    Wrapper round the requests framework to POST to the local ambari server
    """
    if ambhost is None:
        ambhost = thehost
    url = prot + ambhost + ':' + str(port) + api + apath
    # print url
    req = requests.post(url, auth=HTTPBasicAuth(user, passwd), headers={
                        'X-Requested-By': 'ambari'}, data=json.dumps(data))
    return _r2j(req)

ret = ambari_get("clusters")
##################################################################
# Start ambari agents
##################################################################

print "Attempting to start ambari agents on all", len(hosts), "nodes"
sys.stdout.flush()

ambari = lD.remoteHost("root", thehost, access_key)

# Step one, install myself, dsh and deploy ambari agents to all nodes
try:
    ambari.run("which pdsh")
    ambari.run("which curl")
except lD.ShellExecuteError:
    ambari.run("yum -y install epel-release")
    ambari.run("yum clean all")
    ambari.run("yum -y install pdsh curl")

# modify iptables, only in case of Centos6
if ambari.detect_linux_version() in ["Centos6"]:
    ambari.run("service iptables stop")

admin = ambari.run("hostname")

whole_cluster = lD.multiremotes(hosts, jump=ambari)

# Check if all nodes in the cluster are contactable
try:
    whole_cluster.check(firsttime=True)
except lD.ShellExecuteError:
    print "Could not access machines with passwordless ssh, the ambari node must have passwordless ssh access to the " \
          "rest, fix and try again"
    raise

# Verify that all nodes have similar system times
ambtime = int(ambari.run("date -u '+%s'"))
cltime = whole_cluster.run("date -u '+%s'")
cltime = [(int(p.split(':')[-1])) for p in cltime.split('\n')]

if (max(cltime) - min(cltime)) > (10 * 60):
    raise RuntimeError('The system clocks are not synchronized, a difference of ' +
                       str(max(cltime) - min(cltime)) + ' seconds was found')
if min(cltime) < (ambtime - 5):
    raise RuntimeError('At least one machine has a too early system clock, a difference of ' +
                       str(ambtime - min(cltime)) + ' seconds was found')

try:
    if "no ambari-agent" in whole_cluster.run("which ambari-agent"):
        raise lD.ShellExecuteError()
except lD.ShellExecuteError:
    whole_cluster.register()
    whole_cluster.run("yum -y install epel-release")
    # TODO: instead copy this file _from_ the ambari node *to* the others directly
    # For the time being, copy to tmp, then redistribute if necessary
    copy_from = None
    # First handle the localhost case: repo already exists
    atmp = None
    if thehost == "localhost":
        for _repoption in ["/etc/yum.repos.d/ambari.repo", installfrom + "/repo/ambari.repo",
                           installfrom + "/../dev/repo/ambari.repo"]:
            if os.path.exists(_repoption) and os.access(_repoption, os.R_OK):
                copy_from = _repoption
                break
    # Then handle the remote case where repo already exists
    else:
        for _repoption in ["/etc/yum.repos.d/ambari.repo", installfrom + "/repo/ambari.repo",
                           installfrom + "/../dev/repo/ambari.repo"]:
            if "YES" in ambari.run("if [ -e " + _repoption + " ]; then echo 'YES'; fi;"):
                atmp = tempfile.mkdtemp()
                copy_from = atmp + '/ambari.repo'
                ambari.pull(copy_from, _repoption)
                break
    # Then handle the remote case where repo does not yet exist, this would be strange
    if copy_from is None:
        raise IOError("Could not find ambari.repo file! We think this means that ambari was not installed yet"
                      " deploy_from_blueprint.py needs ambari to be installed on the server first")
    whole_cluster.cp(copy_from, "/tmp/ambari.repo")
    # clean tmp file
    if atmp:
        if os.path.exists(atmp) and len(atmp) > 4:
            os.system('rm -rf ' + atmp)

    whole_cluster.run(
        "\"bash -c 'if [ ! -e /etc/yum.repos.d/ambari.repo ] ; then cp /tmp/ambari.repo /etc/yum.repos.d/ambari.repo "
        "; fi; rm -f /tmp/ambari.repo ;'\"")
    try:
        # try and retry
        whole_cluster.run("yum -y install epel-release ambari-agent curl wget")
    except lD.ShellExecuteError:
        time.sleep(5)
        whole_cluster.run("yum -y install epel-release ambari-agent curl wget")

try:
    whole_cluster.run("echo $HOSTNAME")
except lD.ShellExecuteError:
    whole_cluster.register()

# turn off se linux across the cluster ...
if ambari.detect_linux_version() in ["Centos6"]:
    whole_cluster.run("'echo 0 >/selinux/enforce'")
elif ambari.detect_linux_version() in ["Centos7"]:
    whole_cluster.run("setenforce permissive")

# set the ambari node address with a sed/regex
whole_cluster.run(" sed -i 's/hostname=.*/hostname=" + admin + "/' /etc/ambari-agent/conf/ambari-agent.ini")
try:
    whole_cluster.run("ambari-agent restart")
except lD.ShellExecuteError:
    time.sleep(2)
    whole_cluster.run("ambari-agent stop")
    time.sleep(2)
    whole_cluster.run("ambari-agent start")
time.sleep(5)

# Modify permissions of installed ambari agent components
whole_cluster.run('"bash -c \\"if [ -d /var/lib/ambari-agent ]; then if [[ `ambari-agent --version` < \'2.2\' ]]; '
                  ' then mkdir -p /var/lib/ambari-agent/data/tmp;'
                  ' chmod -R 0600 /var/lib/ambari-agent/data;'
                  ' chmod -R a+X /var/lib/ambari-agent/data;'
                  ' chmod -R a+rx /var/lib/ambari-agent/data/tmp; fi; fi;\\""')

whole_cluster.run(
    '"bash -c \\"if ls /var/lib/ambari-agent/keys/*.key 1>/dev/null 2>&1;'
    ' then chmod 0600 /var/lib/ambari-agent/keys/*.key; fi\\""')

##################################################################
# Check that all hosts exist now
##################################################################
ok = False
missing = []
count = 0
while count < 10:
    reghosts = ambari_get("hosts")
    reghosts = [str(i['Hosts']['host_name']) for i in reghosts['items']]
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

# Modify permissions of installed ambari agent components
whole_cluster.run('"bash -c \\"if [ -d /var/lib/ambari-agent ]; then if [[ `ambari-agent --version` < \'2.2\' ]]; '
                  ' then mkdir -p /var/lib/ambari-agent/data/tmp;'
                  ' chmod -R 0600 /var/lib/ambari-agent/data;'
                  ' chmod -R a+X /var/lib/ambari-agent/data;'
                  ' chmod -R a+rx /var/lib/ambari-agent/data/tmp; fi; fi;\\""')

whole_cluster.run(
    '"bash -c \\"if ls /var/lib/ambari-agent/keys/*.key 1>/dev/null 2>&1;'
    ' then chmod 0600 /var/lib/ambari-agent/keys/*.key; fi\\""')

##################################################################
# Add pdsh groups, for all hostgroups
##################################################################
# for entire cluster
clustername = clusterfile.split(os.sep)[-1].split('.')[0]
ambari.run('mkdir -p ~/.dsh/group')


def add_hosts_to_pdsh_group(group, hosts):
    """
    Only add missing hosts into groups in the dsh group files
    """
    path = "~/.dsh/group/" + group
    try:
        exists = ambari.run('cat ' + path)
    except lD.ShellExecuteError:
        exists = []
    for host in hosts:
        if host in exists:
            continue
        ambari.run("echo " + host + " >> " + path)

add_hosts_to_pdsh_group(clustername, hosts)
# for each hostgroup
for group in cluster["host_groups"]:
    hgname = group["name"]
    add_hosts_to_pdsh_group(clustername + '_' + hgname, [ahost["fqdn"] for ahost in group["hosts"]])

##################################################################
# Register blueprint and cluster template
##################################################################
print "Attempting to register blueprint ", blueprint["Blueprints"]["blueprint_name"],
print " and create cluster ", clustername

sys.stdout.flush()

# next, register blueprint by name to the ambari server
cmd = 'blueprints/' + blueprint["Blueprints"]["blueprint_name"] + "?validate_topology=false"
try:
    ret = ambari_post(cmd, data=blueprint)
    if verbose:
        print ret
except requests.exceptions.HTTPError as e:
    print e.response.json()
    if "Server Error" in e.message or "Server Error" in e.response.json()['message']:
        print "Warning: detected server error registering blueprint, trying server restart"
        ambari.run("ambari-server restart")
        ret = ambari_post(cmd, data=blueprint)
    elif "Attempted to create a Blueprint which already exists" in e.response.json()['message']:
        ret = e.response.json()
    elif "specified stack doesn't exist" in e.response.json()['message']:
        raise NameError("Detected error, unable to find this stack," +
                        "did you run patch.sh and restart the server as required?")
    else:
        print "Error registering blueprint"
        raise

# Check if blueprint exists before continuing
registered = ambari_get("blueprints/")
if verbose:
    print registered

if blueprint["Blueprints"]["blueprint_name"] not in [i['Blueprints']['blueprint_name'] for i in registered['items']]:
    print registered
    raise RuntimeError(
        "Blueprint does not exist, take a look yourself with " + "curl --user admin:admin http://" + thehost +
        ":8080/api/v1/blueprints/")

# then add the cluster definition, should start all the processes
try:
    regcluster = ambari_post('clusters/' + clustername, data=cluster)
except requests.exceptions.HTTPError as e:
    print e.response.json()
    if "Server Error" in e.message or "Server Error" in e.response.json()['message']:
        print "Warning: detected server error registering cluster, trying server restart"
        ambari.run("ambari-server restart")
        ret = ambari_post(cmd, data=blueprint)
    elif "Unable to update" in e.response.json()['message']:
        raise NameError("Error detected in spooling up cluster from template, is the template complete? Are you "
                        "missing required services?"
                        )
    elif "Attempted to create a Cluster which already exists" in e.response.json()['message']:
        regcluster = e.response.json()
    else:
        print "Error registering cluster"
        raise


if ("Requests" not in regcluster
        or "status" not in regcluster['Requests']
        or regcluster['Requests']['status'] not in ["IN_PROGRESS", "Accepted", "InProgress"]):
    print regcluster
    print >> sys.stderr, "Detected error registering cluster"
    sys.exit(1)

print("Registration successful, configuration in progress, monitor through the web interface at http://"
      + thehost + ":8080")
print "check clusters with curl --user admin:admin http://" + thehost + ":8080/api/v1/clusters"
print "check hosts with curl --user admin:admin http://" + thehost + ":8080/api/v1/hosts"
