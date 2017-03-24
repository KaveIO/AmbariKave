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
import base
import unittest


class TestAService(base.LDTest):

    def runTest(self):
        """
        The remote_blueprint test ups a dev machine and installs a service simply through service.sh.
        It monitors the status of the service specified with service.sh
        This can only be applied to services which have no forced parameters, i.e. where the default
        parameters work fine and are all that is needed.
        """
        # create remote machine
        import os
        import sys

        lD = self.pre_check()
        known = [s for s, d in base.find_services()]
        self.assertTrue(self.service in known, "The service " + self.service + " is unknown, check the case")
        deploy_dir = os.path.realpath(os.path.dirname(lD.__file__) + '/../')
        ambari, iid = self.deploy_dev()
        self.pull(ambari)
        # restart ganglia and nagios
        if self.branch:
            abranch = self.service
        for restart in ["METRICS_MONITOR", "AMBARI_METRICS", "ZOOKEEPER"]:
            stdout = self.servicesh(ambari, "stop", restart)
        for restart in ["ZOOKEEPER", "AMBARI_METRICS", "METRICS_MONITOR"]:
            self.wait_for_service(ambari, restart)
        import time

        time.sleep(15)
        # install the component on top of the blueprint
        stdout = self.servicesh(ambari, "install", self.service)
        self.assertTrue("IN_PROGRESS" in stdout or "InProgress" in stdout or "status\" : \"Accepted" in stdout,
                        "Was unable to install " + self.service + " through service.sh, (" + ' '.join(
                            ambari.sshcmd()) + ")")
        self.wait_for_service(ambari)
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

