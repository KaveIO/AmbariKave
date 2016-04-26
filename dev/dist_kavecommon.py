#! /usr/bin/env python
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
Copy everything from src/shared into each 2.X.KAVE/services directory
"""
import os
import sys
import shutil

runfrom = os.path.realpath(os.path.dirname(__file__))
# top source location
topsource = runfrom + '/../src/HDP'

# collect list of destinations
topdestination = sys.argv[1]
# print "topsource", topsource, "topdestination", topdestination

stacks = [os.path.join(topsource, o) + "/services" for o in os.listdir(topsource) if
          os.path.isdir(os.path.join(topsource, o))]
# print "stacks",stacks

services = []
for s in stacks:
    services = services + [os.path.join(s, o) for o in os.listdir(s) if os.path.isdir(os.path.join(s, o))]

service_subdirs = [s.replace(runfrom + '/../src', '') + "/package/scripts" for s in services]
# print "service_subdirs",service_subdirs

# collect list of files to copy ...
topcopy = runfrom + '/../src/shared/kavecommon.py'

# print topcopy

# copy from all files to all destinations
for s in service_subdirs:
    thisdest = topdestination + os.sep + s
    # print "running for",s,thisdest
    if os.path.isdir(thisdest):
        # print topcopy,"->",thisdest
        shutil.copy(topcopy, thisdest)
