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
Terminate an iid or remove a volume

kill.py iid iid2 iid3 volid1 volid2 volid3
"""

import sys
import os


installfrom = os.path.realpath(os.path.dirname(__file__))
liblocation = os.path.realpath(installfrom + '/../lib')
sys.path.append(liblocation)

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

if len(sys.argv) < 2:
    print __doc__
    raise IOError("please specify something to kill")

iid_to_kill = [i for i in sys.argv[1:] if i.startswith('i-')]
vol_to_kill = [v for v in sys.argv[1:] if i.startswith('vol-')]
fail = [v for v in sys.argv[1:] if (v not in vol_to_kill and v not in iid_to_kill)]

if len(fail):
    raise ValueError("could not recognise volume or instance from " + fail.__str__())

for iid in iid_to_kill:
    lA.killinstance(iid)

for volID in vol_to_kill:
    lA.killvolume(volID)
