#!/usr/bin/env python
##############################################################################
#
# Copyright 2017 KPMG Advisory N.V. (unless otherwise stated)
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
Deletes clusters and their infrastructure from Cloudbreak

usage: ./kill_clusters.py --name cluster_name/list_of_cluster_names
ex: ./kill_clusters.py --name examplelambda1512132645

params:
    --help/-h - shows this helper message and exits

    --name cluster_name/list_of_cluster_names - Cloudbreak cluster name or list of cluster names, separated by spaces, to be deleted.
        Both the cluster(s) and infrastructure will be deleted.

"""

import cbcommon

def help():
    print (__doc__)

if __name__ == "__main__":
    import sys

    cb = cbcommon.CBDeploy()
    if "--help" in sys.argv or "-h" in sys.argv:
        help()
        sys.exit(0)
    if "--name" in sys.argv:
        clusters = sys.argv[2:]
        for cl in clusters:
            try:
                cb.delete_stack_by_name(cl)
            except Exception as e:
                print ("ERROR: ", e)
