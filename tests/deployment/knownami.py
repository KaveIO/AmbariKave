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


class DepKnown(base.LDTest):
    ostype = "Redhat7"

    def runTest(self):
        """
        Create a single centos7 instance with a script, and check that it is contactable at the end, including the
        ambari server running there
        """
        import os

        lD = self.pre_check()
        deploy_dir = os.path.realpath(os.path.dirname(lD.__file__) + '/../')
        self.service = "Deploy"
        ambari, iid = self.deploy_os(self.ostype)
        stdout = ambari.run("echo Hello world from $HOSTNAME")
        self.assertTrue("ambari" in stdout or "test-" in stdout.lower(),
                        "Unable to contact " + ' '.join(ambari.sshcmd()) + "\n" + stdout)
        # Test adding more space with add_new_ebs_volume
        stdout = lD.run_quiet(deploy_dir + "/aws/add_ebsvol_to_instance.py --not-strict " + iid +
                              ' \'{"Mount": "/tmp/testdir1", "Size": 1, "Attach": "/dev/sdf"}\'')
        stdout = ambari.run("ls -l /tmp/testdir1")
        self.assertFalse("No such file or directory" in stdout,
                         "Unable to crate/mount /dev/sdf " + ' '.join(ambari.sshcmd()) + "\n" + stdout)


def suite(verbose=False, ostype="Centos7"):
    suite = unittest.TestSuite()
    test = DepKnown()
    test.debug = verbose
    test.ostype = ostype
    suite.addTest(test)
    return suite


if __name__ == "__main__":
    verbose = False
    if "--verbose" in sys.argv:
        verbose = True
    ostype = "Centos7"
    if len(sys.argv) > 1:
        ostype = sys.argv[1]
    base.run(suite(verbose, ostype=ostype))
