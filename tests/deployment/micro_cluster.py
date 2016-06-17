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


class MicroCluster(base.LDTest):

    def runTest(self):
        """
        Create a small cloudformation cluster.
        This checks slightly more than the single_machine_cluster.py since it also
        verifies the local DNS is working afterwards.
        """
        import os

        lD = self.pre_check()
        deploy_dir = os.path.realpath(os.path.dirname(lD.__file__) + '/../')
        blueprint_dir = os.path.realpath(os.path.dirname(__file__) + '/blueprints/')
        import kaveaws as lA
        clusterfile = "micro.aws.json"
        stdout = self.deploycluster(blueprint_dir + '/' + clusterfile, cname="TestDeploy")
        self.assertTrue(stdout.strip().split("\n")[-2].startswith("Complete, created:"),
                        "failed to generate cluster, \n" + stdout)
        ahost, iid = self.remote_from_cluster_stdout(stdout, mname="testing-001")
        ahost.register()
        stdout = ahost.run("cat /etc/resolv.conf")
        self.assertTrue("kave.io" in stdout,
                        "Incomplete resolv.conf, did you create a new vpc with a correct DNS? ("
                        + ' '.join(ahost.sshcmd()) + ")")
        ahost.run("yum -y install bind-utils")
        stdout = ahost.run("host ns.kave.io")
        self.assertTrue("has address" in stdout, "Lookup broken on ns.kave.io! ("
                        + ' '.join(ahost.sshcmd()) + ")")
        stdout = ahost.run("host testing-001.kave.io")
        self.assertTrue("has address" in stdout, "Lookup broken on testing-001.kave.io! ("
                        + ' '.join(ahost.sshcmd()) + ")")
        stdout = ahost.run("host test-001.kave.io")
        self.assertTrue("has address" in stdout, "Lookup broken on test-001.kave.io! ("
                        + ' '.join(ahost.sshcmd()) + ")")
        import kaveaws as lA

        priv_ip = lA.priv_ip(iid)
        stdout = ahost.run("host " + priv_ip)
        self.assertTrue("domain name pointer" in stdout,
                        "Reverse lookup broken on testing-001.kave.io! ("
                        + ' '.join(ahost.sshcmd()) + ")")


def suite(verbose=False, branch="__local__"):
    suite = unittest.TestSuite()
    test = MicroCluster()
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
