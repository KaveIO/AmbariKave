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
import unittest, sys
import base


class SingleMachineCluster(base.LDTest):
    def runTest(self):
        """
        Create a single centos instance with the up_aws_cluster script, the minimal test of this script
        """
        import os

        lD = self.preCheck()
        deploy_dir = os.path.realpath(os.path.dirname(lD.__file__) + '/../')
        stdout = lD.runQuiet(
            deploy_dir + "/aws/up_aws_cluster.py TestDeploy " + deploy_dir + "/clusters/single.aws.json --not-strict")
        self.assertTrue(stdout.strip().split("\n")[-2].startswith("Complete, created:"),
                        "failed to generate cluster, \n" + stdout)


def suite(verbose=False):
    suite = unittest.TestSuite()
    test = SingleMachineCluster()
    test.debug = verbose
    suite.addTest(test)
    return suite


if __name__ == "__main__":
    verbose = False
    if "--verbose" in sys.argv:
        verbose = True
    base.run(suite(verbose))