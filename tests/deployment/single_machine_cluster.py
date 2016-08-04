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
import unittest
import sys
import base


class SingleMachineCluster(base.LDTest):

    def runTest(self):
        """
        Create a single centos instance with the up_aws_cluster script, the minimal test of this script
        """
        import os

        lD = self.pre_check()
        deploy_dir = os.path.realpath(os.path.dirname(lD.__file__) + '/../')
        import kaveaws as lA
        region = lA.detect_region()
        clusterfile = "single.aws.json"
        cstdout = self.deploycluster(deploy_dir + "/clusters/" + clusterfile, cname="TestDeploy")
        self.assertTrue(cstdout.strip().split("\n")[-2].startswith("Complete, created:"),
                        "failed to generate cluster, \n" + cstdout)
        ambari, iid = self.remote_from_cluster_stdout(cstdout)
        ambari.register()
        self.wait_for_ambari(ambari, check_inst=["inst.stdout", "inst.stderr"])
        # Check multiremote functionality
        allremotes, iids = self.multiremote_from_cluster_stdout(cstdout)
        allremotes.cp(deploy_dir + '/remotescripts/add_incoming_port.py', 'testtest.py')
        self.assertTrue("testtest.py" in ambari.run("ls -l"), "pdcp failed to work properly")
        # Check multiremote functionality with jump intermediate
        allremotes.jump = ambari
        allremotes.hosts=['ssh:root@ambari']
        allremotes.cp(deploy_dir + '/remotescripts/add_incoming_port.py', 'testtest3.py')
        self.assertTrue("testtest3.py" in ambari.run("ls -l"), "pdcp via jump failed to work properly")
        self.assertTrue("testtest3.py" in allremotes.run("ls -l"), "ls via jump failed to work properly")


def suite(verbose=False, branch="__local__"):
    suite = unittest.TestSuite()
    test = SingleMachineCluster()
    test.debug = verbose
    test.branch = branch
    test.branchtype = branch
    suite.addTest(test)
    return suite


if __name__ == "__main__":
    verbose = False
    if "--verbose" in sys.argv:
        verbose = True
    branch = "__local__"
    if "--branch" in sys.argv:
        branch = "__service__"
        sys.argv = [s for s in sys.argv if s != "--branch"]
    if "--this-branch" in sys.argv:
        branch = "__local__"
        sys.argv = [s for s in sys.argv if s != "--this-branch"]
    base.run(suite(verbose, branch))
