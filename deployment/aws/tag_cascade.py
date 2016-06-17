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
Tag a set of aws resources

usage: tag_cascade.py resourceid '{"TagName" : "TagValue"}' [--no-cascade] [--verbose]

tag_cascade is supposed to be used to tag all associated resources with
a given set of tags, to enable simpler tracking of costs on aws

For example:

tag_cascade.py existing-vpc-id '{"Project" : "AmbariKave"}'

Will begin at the vpc, and tag all related security groups/subnets,
then cascade the tags through to all machines living within those groups
and then continue to tag all associated volumes of those instances

The --no-cascade flag can be used if the user just wants to tag one resource and stop there

Otherwise, if the resource is a vpc, it will cascade to all subgroups/subnets/machines/volumes
if the resource is a subgroup or subnet it will cascade to all machines/volumes
if the resource is an instance, it will cascade to all volumes

The dictionary string of tags to add must be valid json
"""

import sys
import os
import json

installfrom = os.path.realpath(os.path.dirname(__file__))
liblocation = os.path.realpath(installfrom + '/../lib')
sys.path.append(liblocation)

import kavedeploy as lD


def help():
    print __doc__

cascade = True


def check_opts():
    global cascade
    if "-h" in sys.argv or "--help" in sys.argv:
        help()
        sys.exit(0)
    if "--verbose" in sys.argv:
        lD.debug = True
        sys.argv = [s for s in sys.argv if s != "--verbose"]
    else:
        lD.debug = False
    if "--no-cascade" in sys.argv:
        cascade = False
        sys.argv = [s for s in sys.argv if s != "--no-cascade"]
    if len(sys.argv) < 3:
        help()
        raise AttributeError("You did not supply enough parameters")
    if len(sys.argv) > 3:
        help()
        raise AttributeError("You supplied too many parameters")


check_opts()

import kaveaws as lA
import json

lA.testaws()

resources = [sys.argv[1]]
tag_dict = json.loads(sys.argv[2])

# Find all associated resources
if cascade:
    print "Collecting cascade resources"
    resources = lA.find_all_child_resources(resources[0])

# Tag everything
print "Tagging"
lA.tag_resources(resources, tag_dict)
