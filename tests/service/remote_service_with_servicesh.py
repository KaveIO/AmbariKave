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
import base
import unittest


class TestAService(base.LDTest):

    def runTest(self):
        # create remote machine
        import os
        import sys

        lD = self.preCheck()
        known = [s for s, d in base.findServices()]
        self.assertTrue(self.service in known, "The service " + self.service + " is unknown, check the case")
        deploy_dir = os.path.realpath(os.path.dirname(lD.__file__) + '/../')
        ambari, iid = self.deployDev()
        # restart ganglia and nagios
        if self.branch:
            abranch = self.service
        for restart in ["GANGLIA", "NAGIOS"]:
            stdout = self.servicesh(ambari, "stop", restart)
        for restart in ["GANGLIA", "NAGIOS"]:
            self.waitForService(ambari, restart)
        import time

        time.sleep(15)
        # install the component on top of the blueprint
        stdout = self.servicesh(ambari, "install", self.service)
        self.assertTrue("InProgress" in stdout,
                        "Was unable to install " + self.service + " through service.sh, (" + ' '.join(
                            ambari.sshcmd()) + ")")
        self.waitForService(ambari)
        return self.check(ambari)


if __name__ == "__main__":
    import sys

    verbose = False
    if "--verbose" in sys.argv:
        verbose = True
        sys.argv = [s for s in sys.argv if s != "--verbose"]
    branch = "__local__"
    if "--branch" in sys.argv:
        branch = "__service__"
        sys.argv = [s for s in sys.argv if s != "--branch"]
    if "--this-branch" in sys.argv:
        branch = "__local__"
        sys.argv = [s for s in sys.argv if s != "--this-branch"]
    if len(sys.argv) < 2:
        raise KeyError("You must specify which service to test")
    service = sys.argv[1]
    test = TestAService()
    test.service = service
    test.branch = branch
    test.debug = verbose
    test.checklist = []
    if len(sys.argv) > 2:
        test.checklist = sys.argv[2:]
    suite = unittest.TestSuite()
    suite.addTest(test)
    base.run(suite)
