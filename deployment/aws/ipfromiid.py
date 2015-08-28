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
Very simple script, returns an ip address from an aws iid or list of iids

usage ipfromiid.py iid [iid iid iid ...]

If instance is not yours/does not exist, prints "NoInstance"
If instance has no IP assigned, prints "NoIP"
"""
import sys
import os


installfrom = os.path.realpath(os.path.dirname(__file__))
liblocation = os.path.realpath(installfrom + '/../lib')
sys.path.append(liblocation)

if "--help" in sys.argv or "-h" in sys.argv:
    print __doc__
    sys.exit(0)

import kavedeploy as lD
import kaveaws as lA

ips = ""
for iid in sys.argv[1:]:
    if len(ips):
        ips = ips + " "
    try:
        ip = lA.pubIP(iid)
        if ip is None:
            ips = ips + "NoIP"
        else:
            ips = ips + str(ip)
    except ValueError:
        ips = ips + "NoInstance"
print ips
