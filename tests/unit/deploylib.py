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
import unittest
import base


class TestDeployLib(unittest.TestCase):
    def runTest(self):
        """
        Tests which do not need any environment parameters or access to aws
        """
        import libDeploy as lD

        lD.testproxy()
        self.assertIsNot(lD.which("ls"), None)
        self.assertRaises(RuntimeError, lD.runQuiet, ("thisisnotacommand"))
        stdout = lD.runQuiet(['which', 'ls'], shell=False)
        self.assertTrue('/bin/ls' in stdout)
        self.assertIsNot(lD.which("pdsh"), None,
                         "pdsh is not installed, please install it in order to test the multiremotes functionality, "
                         "sudo yum -y install pdsh")
        lD.runQuiet("touch /tmp/fake_test_ssh_key.pem")
        lD.runQuiet("chmod 400 /tmp/fake_test_ssh_key.pem")
        test = lD.remoteHost("root", "test", '/tmp/fake_test_ssh_key.pem')
        test = lD.multiremotes([test.host], access_key='/tmp/fake_test_ssh_key.pem')


class TestJSON(unittest.TestCase):
    def runTest(self):
        """
        Checks that every json file under the deployment or tests dir is correct json!
        """
        import libDeploy as lD
        import os

        deploydir = os.path.dirname(lD.__file__)
        testdir = os.path.dirname(__file__)
        import glob, json

        jsons = glob.glob(deploydir + "/*/*.json") + glob.glob(testdir + "/../*/*.json") + glob.glob(
            testdir + "/../*/*/*.json")
        for ason in jsons:
            #print ason
            f = open(ason)
            l = f.read()
            f.close()
            self.assertTrue(len(l) > 1, "json file " + ason + " is a fragment or corrupted")
            try:
                interp = json.loads(l)
            except:
                self.assertTrue(False, "json file " + ason + " is not complete or not readable")


def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestDeployLib())
    suite.addTest(TestJSON())
    return suite


if __name__ == "__main__":
    base.run(suite())