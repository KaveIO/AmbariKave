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
###############################################################################
# print the list of services and their hosts
# usage in stand-alone script: libScan.py [hostname=localhost] [username=admin] [password=admin]

#
# Library to evaluate mathematical expressions
# Obtained as example from http://stackoverflow.com/questions/2371436/evaluating-a-mathematical-expression-in-a-string
# Thanks to stackoverflow user J.F. Sebastian
#
import ast
import operator as op

# supported operators
operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
             ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
             ast.USub: op.neg}

def eval_expr(expr):
    """
    >>> eval_expr('2^6')
    4
    >>> eval_expr('2**6')
    64
    >>> eval_expr('1 + 2*3**(4^5) / (6 + -7)')
    -5.0
    """
    return eval_(ast.parse(expr, mode='eval').body)

def eval_(node):
    if isinstance(node, ast.Num): # <number>
        return node.n
    elif isinstance(node, ast.BinOp): # <left> <operator> <right>
        return operators[type(node.op)](eval_(node.left), eval_(node.right))
    elif isinstance(node, ast.UnaryOp): # <operator> <operand> e.g., -1
        return operators[type(node.op)](eval_(node.operand))
    else:
        raise TypeError(node)

#######################################################################
import subprocess
import kavecommon as kc
import json, os, sys

#ambari, by default, has admin:admin as the username/password combination, but this is changable with the correct
# options
default_ambari_user = "admin"
default_ambari_password = "admin"

# here we need to manually enter everything we want to be able to find through the configurations
# syntax is { "SERVICE_NAME" : { "quick_link_name" : port_list }}
# port_list is [default port , "path/to/configuration.if.set"]
# the default port should always be given, even if it is 80
# Simple addition, subtraction and multiplication is supported, when separated with a space from the parameter
#  ["apache/APACHE_PORT +1000"] would return the result of adding 1000 to the apache port if set
service_portproperty_dict = {"GANGLIA_SERVER": {"monitor": ["80/ganglia"]},
                             "NAGIOS_SERVER": {"alerts": ["80/nagios"]},
                             "AMBARI_SERVER": {"admin": [8080]},
                             "JENKINS_MASTER": {"jenkins": [8080, "jenkins/JENKINS_PORT"]},
                             "JBOSS_APP_SERVER": {"jboss": [8080, "jboss/http_port"]},
                             "ARCHIVA_SERVER": {"archiva": [5050, "archiva/archiva_jetty_port"]},
                             "SONARQUBE_SERVER": {"sonar": [5051, "sonarqube/sonar_web_port"]},
                             "APACHE_WEB_MASTER": {"webpage": [80, "apache/PORT"]},
                             "TWIKI_SERVER": {"twiki": ["80/twiki"]},
                             "MONGODB_MASTER": {"mongo_tcp": [27017, "mongodb/tcp_port"], "mongo_web" : [28017, "mongodb/tcp_port +1000"]},#need to add 1000 to the port number if it exists!
                             "GITLAB_SERVER": {"gitlab": [80, "gitlab/gitlab_port"]},
                             "STORMSD_UI_SERVER": {"storm": [8744, "stormsd/ui.port"]},
                             "HUE_SERVER": {"hue": [8744, "hue/web_ui_port"]},
                             "FREEIPA_SERVER": {"users": [80]},
                             "NAMENODE": {"hdfs_nn1": [50070]},
                             "SECONDARY_NAMENODE": {"hdfs_nn2": [50090]},
                             "RESOURCEMANAGER": {"yarn": [8088]}
                             }


def apiquery(request, host="localhost", exit=True, user=None, passwd=None, JSON=True, part="items"):
    """
    Get the result from a rest query to the ambari api. Runs curl.
    request: the api call that should come after "http://host:8080/api/v1/"
    exit->implies the failure of the call will raise an exception
    user authenticates to ambari, i.e. 'admin'
    passwd authenticates to ambari, i.e. 'admin'
    JSON: interpret the result as json (default) and return only json["part"] of the query to avoid needing to call
    "items" everywhere
    None as part implies return whole result.
    """
    if user is None:
        user = default_ambari_user
    if passwd is None:
        passwd = default_ambari_password
    response = kc.mycmd(
        "curl -H 'X-Requested-By:" + user + "' --user " + user + ":" + passwd + " http://" + host + ":8080/api/v1/" +
        request)
    response = response[1]  #stdout
    if not JSON:
        return response
    if part is None:
        return json.loads(response)
    return json.loads(response)[part]


def host_to_hostgroup(host_components, blueprint):
    """
    Based on a list of host components, match a host to where it sits in the blueprint
    returns the host_group name, or none
    """
    for group in blueprint["host_groups"]:
        #print group
        blueprint_components = [c["name"] for c in group["components"]]
        missing = [c for c in host_components if c not in blueprint_components and c != "AMBARI_SERVER"]
        extra = [c for c in blueprint_components if c not in host_components and c != "AMBARI_SERVER"]
        if len(missing) or len(extra):
            continue
        return group["name"]
    return None


def cloneconfdict(cdictfrom, cdictto):
    """
    clone all entries of adict from into adictto, assuming it looks like { "name" : { "prop" : val } }
    """
    for key, cdict in cdictfrom.iteritems():
        if key not in cdictto:
            cdictto[key] = {}
        for key2, val in cdictfrom[key].iteritems():
            cdictto[key][key2] = val
    return cdictto


def resolve_config(blueprint, hostgroup):
    """
    Resolve the configurations of all things in this host group, first by taking any global configurations,
    and next by overwriting any set in the host group's own configurations
    """
    configurations = {}
    for bpc in blueprint["configurations"]:
        cloneconfdict(bpc, configurations)
    for bph in blueprint["host_groups"]:
        if bph["name"] != hostgroup:
            continue
        if "configurations" not in bph:
            continue
        for bpc in bph["configurations"]:
            cloneconfdict(bpc, configurations)
    #print configurations
    return configurations


def pickprop(myconfigs, tofind):
    """
    Given a full configuration dictionary, and a tofind list, which looks like [default, "service/propertyname"]
    return the property requested, i.e. [8080] returns [8080], [80, "apache/APACHE_PORT"] returns the value set for
    APACHE_PORT or 80 if unset
    Simple addition, subtraction and multiplication is supported (when separated by a space):
    ["apache/APACHE_PORT +1000"] would return the result of adding 1000 to the apache port if set
    """
    #print "looking for", tofind
    #print "in", myconfigs
    default_port = tofind[0]
    if len(tofind) == 1:
        #print "no alternate suggested"
        return default_port
    prop = tofind[-1]
    comppath = prop.split(" ")[0].split("/")[0]
    compprop = prop.split(" ")[0].split("/")[-1]
    arithmetic = ''
    if " " in prop:
        arithmetic=''.join(prop.split(" ")[1:])
    #print comppath, compprop
    #print myconfigs.keys()
    if comppath not in myconfigs:
        #print "no comppath"
        return default_port
    #print myconfigs[comppath]
    if not len([c == compprop for c in myconfigs[comppath]]):
        #print "no comprop", myconfigs[comppath]
        return default_port
    if not len(arithmetic):
        return myconfigs[comppath][compprop]
    return eval_expr(myconfigs[comppath][compprop]+arithmetic)


def collect_config_data(ambari="localhost", user=None, passwd=None, ):
    """
    Resolves the blueprint and the host information from an ambari server to return:
    (cluster_service_host, cluster_host_service, cluster_service_link)
    cluster_service_host: dictionary of {"cluster": {"service":[hosts]}}
    cluster_host_service: dictionary of {"cluster": {"host":[services]}}
    cluster_service_link: dictionary of {"cluster": {"service":[links]}}
    uses the globally set dictionary of ports and configurable parameters to determine what should be a link and what
    shouldn't
    """
    #####  Check host is reachable
    response = apiquery("clusters -i -I", exit=False, JSON=False, host=ambari, user=user, passwd=passwd)
    if "200 OK" not in response:
        raise NameError("Host could not be contacted, is Ambari running there? " + ambari)

    cluster_service_host = {}
    cluster_host_service = {}
    cluster_service_link = {}

    clusters = apiquery("clusters", host=ambari)
    clusterlist = [str(c["Clusters"]["cluster_name"]) for c in clusters]
    #print clusterlist

    for cluster in clusterlist:
        cluster_service_host[cluster] = {}
        cluster_host_service[cluster] = {}
        cluster_service_link[cluster] = {}
        hosts = apiquery("clusters/" + cluster + "/hosts", host=ambari, user=user, passwd=passwd)
        blueprint = apiquery("clusters/" + cluster + "?format=blueprint", host=ambari, part=None, user=user,
                             passwd=passwd)
        #print blueprint
        hostlist = [str(h["Hosts"]["host_name"]) for h in hosts]
        #print hostlist
        for host in hostlist:
            host_components = apiquery("clusters/" + cluster + "/hosts/" + host, part="host_components", host=ambari,
                                       user=user, passwd=passwd)
            #print host_components
            components = [str(h["HostRoles"]["component_name"]) for h in host_components]
            hostgroup = host_to_hostgroup(components, blueprint)
            myconfigs = resolve_config(blueprint, hostgroup)


            #try adding AMBARI_SERVER if it's there in the hostgroup...
            bp_components=[]
            for group in blueprint["host_groups"]:
                #print group
                if group["name"]==hostgroup:
                    bp_components=[c["name"] for c in group["components"]]
            if "AMBARI_SERVER" in bp_components:
                components.append("AMBARI_SERVER")

            cluster_host_service[cluster][host] = components

            #print components
            for component in components:
                if component not in cluster_service_host[cluster]:
                    cluster_service_host[cluster][component] = [host]
                else:
                    cluster_service_host[cluster][component].append(host)
                if component in service_portproperty_dict:
                    if component not in cluster_service_link[cluster]:
                        cluster_service_link[cluster][component] = []
                    for linkname, port in service_portproperty_dict[component].iteritems():
                        cluster_service_link[cluster][component].append(
                            "<a href='http://" + host.split('.')[0] + ":" + str(
                                pickprop(myconfigs, port)) + "'>" + linkname + "</a> ")

    #Fallback: add ambari where the nagios server is...
    for cluster in clusterlist:
        if "NAGIOS_SERVER" in cluster_service_host[cluster] and "AMBARI_SERVER" not in cluster_service_host[cluster]:
            cluster_service_host[cluster]["AMBARI_SERVER"] = cluster_service_host[cluster]["NAGIOS_SERVER"]
            if "AMBARI_SERVER" in service_portproperty_dict and "AMBARI_SERVER" in cluster_service_host[cluster]:
                cluster_service_link[cluster]["AMBARI_SERVER"] = []
                for linkname, port in service_portproperty_dict["AMBARI_SERVER"].iteritems():
                    cluster_service_link[cluster]["AMBARI_SERVER"].append("<a href='http://"
                                                                          + cluster_service_host[cluster]["AMBARI_SERVER"][0].split('.')[0]
                                                                          + ":" + str(pickprop(myconfigs, port)) + "'>" + linkname + "</a>")

    #print cluster_service_host
    #print cluster_host_service
    #print cluster_service_link
    return cluster_service_host, cluster_host_service, cluster_service_link


def pretty_print(cluster_service_host, cluster_host_service, cluster_service_link, format="plain"):
    """
    Pretty print the list of components, either as human-readable, or as html
    format= plain or html
    """
    retstr = ""
    format = format.lower()
    if format not in ["html", "plain"]:
        raise ValueError("Only html or plain formats known, not " + format)
    clusterlist = cluster_service_host.keys()
    for cluster in clusterlist:
        if format == "plain":
            retstr = retstr + "==================\n"
            retstr = retstr + "* '" + cluster + "' cluster \n"
        else:
            retstr = retstr + "<h3><font size=5px>'" + cluster + "' cluster</font></h3>\n"
        masters_with_links = [service for service in cluster_service_host[cluster] if
                              ("SERVER" in service or "MASTER" in service or "NAMENODE" in service or "MANAGER" in service) and (
                              service in cluster_service_link[cluster])]
        masters_without_links = [service for service in cluster_service_host[cluster] if
                                 ("SERVER" in service or "MASTER" in service or "NAMENODE" in service or "MANAGER" in service) and (
                                 service not in cluster_service_link[cluster]) and (service not in masters_with_links)]
        others = [service for service in cluster_service_host[cluster] if
                  service not in (masters_without_links + masters_with_links)]
        #first print services with links!
        if format == "plain":
            retstr = retstr + "|--* Servers \n"
        else:
            retstr = retstr + "<b>Servers</b><p><ul>\n"
        for service in masters_with_links:
            sprint=service
            if "_" in service:
                sprint=' '.join(service.split("_")[:-1])
            sprint=sprint.upper()[0]+sprint.lower()[1:]
            if format == "plain":
                retstr = retstr + "|  |--* "
            else:
                retstr = retstr + "  <li>"
            retstr = retstr + sprint + " "
            for link in cluster_service_link[cluster][service]:
                retstr = retstr + link
            if format == "plain":
                retstr = retstr + "\n"
            else:
                retstr = retstr + "</li>\n"
        #then print masters without links
        for service in masters_without_links:
            sprint=service
            if "_" in service:
                sprint=' '.join(service.split("_")[:-1])
            sprint=sprint.upper()[0]+sprint.lower()[1:]
            if format == "plain":
                retstr = retstr + "|  |--* "
            else:
                retstr = retstr + "  <li>"
            retstr = retstr + sprint + " "
            retstr = retstr + "(" + cluster_service_host[cluster][service].__str__() + ")"
            if format == "plain":
                retstr = retstr + "\n"
            else:
                retstr = retstr + "</li>\n"
        #then print clients

        if format == "plain":
            retstr = retstr + "|\n"
            retstr = retstr + "|--* Clients \n"
        else:
            retstr = retstr + "</ul><p><b>Clients</b><p><ul>\n"
        for host in cluster_host_service[cluster]:
            if format == "plain":
                retstr = retstr + "|  |--* "
            else:
                retstr = retstr + "  <li>"
            retstr = retstr + host + " " + [c.lower() for c in cluster_host_service[cluster][host] if c in others].__str__()
            if format == "plain":
                retstr = retstr + "\n"
            else:
                retstr = retstr + "</li>\n"
        if format == "html":
            retstr = retstr + "</ul>\n"

    return retstr


if __name__ == "__main__":
    ambari = "localhost"
    format = "plain"
    user = None
    passwd = None
    if "html" in sys.argv:
        format = "html"
        sys.argv = [s for s in sys.argv if s != "html"]
    if len(sys.argv) > 1:
        ambari = sys.argv[1]
    if len(sys.argv) > 2:
        user = sys.argv[2]
    if len(sys.argv) > 3:
        passwd = sys.argv[3]
    if len(sys.argv) > 4:
        raise ValueError("Too many arguments!")

    cluster_service_host, cluster_host_service, cluster_service_link = collect_config_data(ambari, user=user,
                                                                                           passwd=passwd)

    print "Welcome to your KAVE"
    print pretty_print(cluster_service_host, cluster_host_service, cluster_service_link, format=format)

#####  Get Services from the blueprint

