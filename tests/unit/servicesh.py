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
import base


class TestServiceSH(unittest.TestCase):

    def runTest(self):
        """
        Each service must appear twice in service.sh
        """
        # this list is a list of things that you can't install with service.sh, probably because the service has
        # multiple components
        ignore_services = ["KAVEZOE"]
        # find the name of all our services
        # check they exist at least twice in service.sh
        import os
        import sys

        dir = os.path.realpath(os.path.dirname(__file__) + "/../../")
        # check they exist at least twice in service.sh
        import kavedeploy as lD

        lD.debug = False
        for service, sdir in base.find_services():
            if service in ignore_services:
                continue
            cmd = "grep -e " + service + " " + dir + "/bin/service.sh" + " | wc -l"
            stdout = lD.run_quiet(cmd)
            count = int(stdout.strip())
            self.assertTrue(count >= 2, "Not enough copies of " + service + " in service.sh")


def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestServiceSH())
    return suite


if __name__ == "__main__":
    base.run(suite())
