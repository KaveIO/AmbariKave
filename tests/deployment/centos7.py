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
import unittest
import sys
import base


class DepCentos7(base.LDTest):

    def runTest(self):
        """
        Create a single centos7 instance with a script, and check that it is contactable at the end, including the
        ambari server running there
        """
        import os

        lD = self.preCheck()
        deploy_dir = os.path.realpath(os.path.dirname(lD.__file__) + '/../')
        self.service = "Deploy"
        self.ostype = "Centos7"
        ambari, iid = self.deployOS(self.ostype)
        if self.ostype.startswith("Ubuntu"):
            ambari.run('apt-get update')
        stdout = ambari.run("echo Hello world from $HOSTNAME")
        self.assertTrue("ambari" in stdout or "Test-" in stdout,
                        "Unable to contact " + ' '.join(ambari.sshcmd()) + "\n" + stdout)


def suite(verbose=False):
    suite = unittest.TestSuite()
    test = DepCentos7()
    test.debug = verbose
    suite.addTest(test)
    return suite


if __name__ == "__main__":
    verbose = False
    if "--verbose" in sys.argv:
        verbose = True
    base.run(suite(verbose))
