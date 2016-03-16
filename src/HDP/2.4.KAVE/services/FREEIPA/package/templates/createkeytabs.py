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
This is the createkeytabs script of teh KAVE FreeIPA implementation

usage:
    kinit admin
    createkeytabs.py kerberos.csv

instructions:
   MUST be run from the ambari node, where FreeIPA is also installed, as the root user
   kinit [someadminuser] must be called beforehand
   - because only the ambari node root user can ssh over the whole cluster
   - because it's best to create all the users/keytabs on the admin node
   - because kinit is necessary to authenticate with FreeIPA

explanation:
   The Ambari kerberization process gives you the chance to download a csv
   containing a list of needed keytabs. This keytabs file lists all the bits
   and pieces HDFS/yarn components need to operate a fully kerberized cluster.
   Late creation of these keytabs is better, the list is likely to change.

operation:
   For each line in the kerberos.csv file
   a) Check that the machine named exists within the cluster
   b) Check/fix that the user named exists with the named group

   Then split the kerberos.csv entries into two types, headless and service
   c) Create any user principles / headless keytabs and control permissions
   d) Copy headless keytabs to all machines and control permissions

   e) Create service principles and keytabs and control permissions
   f) Copy keytabs to required machines and control permissions

   g) Check: su <user> /usr/bin/kinit -kt <keytab>
"""
import sys
import os
try:
    import freeipa
except ImportError:
    sys.path.append("{{scriptpath}}")
    import freeipa

if __name__=="__main__":
    ipa = freeipa.FreeIPACommon()
    print sys.argv[-1]
    if "--help" in sys.argv:
        print __doc__
        sys.exit(0)
    # simple test that this works
    ipa.group_exists('admins')

