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
Deploys KAVE cluster from given blueprint via Cloudbreak

usage: ./cbdeploy.py blueprint_name/list_of_blueprints/--all [--kill-passed/--kill-failed/--kill-all] [--verbose]
ex: ./cbdeploy.py AIRFLOW

params:
    --help/-h - shows this helper message and exits

    blueprint_name/list_of_blueprints/--all - the script needs a valid blueprint name in order to deploy a cluster.
        It can also take a list of blueprint names, separated by spaces, as parameter to deploy clusters simultaneously,
        or an --all parameter, which would deploy all clusters described in the blueprints folder at once.

    --this-branch - if present, local Git repo will be used for Ambari patching

    --kill-passed - if present, all successfully deployed clusters will be deleted after deployment is complete

    --kill-failed - if present, all clusters which reported failure will be deleted after deployment is complete

    --kill-all - if present, all clusters will be deleted after deployment is complete

    --verbose - if present, more detailed information about stack and cluster status will be shown during deployment.

"""

import time
import cbcommon

def help():
    print __doc__

if __name__ == "__main__":
    import sys
    import glob
    from threading import Thread

    disabled = []
    kill_passed_clusters = False
    kill_failed_clusters = False
    kill_all_clusters = False
    verbose_enabled = False
    local_repo = False

    cb = cbcommon.CBDeploy()
    if not cb.access_token:
        sys.exit("FAILURE: Missing Cloudbreak access token.")

    if "--help" in sys.argv or "-h" in sys.argv:
        help()
        sys.exit(0)
    if sys.argv.__len__() < 2:
        print "ERROR: Blueprint name not specified"
        help()
        sys.exit(0)
    if "--all" in sys.argv:
        blueprints = glob.glob("blueprints/*.blueprint.json")
        blueprints = [b.split("/")[-1].split(".")[0] for b in blueprints]
        blueprints = [b for b in blueprints if b not in disabled]
    else:
        blueprints = [bp for bp in sys.argv[1:] if not (bp.startswith(
            "--kill-") or bp.startswith("--verbose") or bp.startswith("--this-branch"))]
    if "--kill-passed" in sys.argv:
        kill_passed_clusters = True
    if "--kill-failed" in sys.argv:
        kill_failed_clusters = True
    if "--kill-all" in sys.argv:
        kill_all_clusters = True
    if "--verbose" in sys.argv:
        verbose_enabled = True
    if "--this-branch" in sys.argv:
        local_repo = True

    for i in range(0, len(blueprints)):
        print "Starting cluster deployment for blueprint " + blueprints[i]
        t = Thread(target=cb.wait_for_cluster, args=(blueprints[i],), kwargs={
                   "local_repo": local_repo,
                   "kill_passed": kill_passed_clusters,
                   "kill_failed": kill_failed_clusters,
                   "kill_all": kill_all_clusters,
                   "verbose": verbose_enabled})
        t.start()
        time.sleep(20)
