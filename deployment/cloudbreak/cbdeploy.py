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
import time
import cbcommon

if __name__ == "__main__":
    import sys
    import glob
    from threading import Thread

    disabled = []
    kill_passed_clusters = False
    kill_failed_clusters = False
    kill_all_clusters = False
    verbose_enabled = False

    cb = cbcommon.CBDeploy()
    if "--all" in sys.argv:
        blueprints = glob.glob("blueprints/*.blueprint.json")
        blueprints = [b.split("/")[-1].split(".")[0] for b in blueprints]
        blueprints = [b for b in blueprints if b not in disabled]
    else:
        blueprints = [bp for bp in sys.argv[1:] if not (bp.startswith("--kill-") or bp.startswith("--verbose"))]
    if "--kill-passed" in sys.argv:
        kill_passed_clusters = True
    if "--kill-failed" in sys.argv:
        kill_failed_clusters = True
    if "--kill-all" in sys.argv:
        kill_all_clusters = True
    if "--verbose" in sys.argv:
        verbose_enabled = True

    for i in range(0, len(blueprints)):
        print "Start cluster deployment for blueprint " + blueprints[i]
        t = Thread(target=cb.wait_for_cluster, args=(blueprints[i],), kwargs={
                   "kill_passed": kill_passed_clusters, "kill_failed": kill_failed_clusters, "kill_all": kill_all_clusters,
                   "verbose": verbose_enabled})
        t.start()
        time.sleep(20)
